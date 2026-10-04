from __future__ import annotations
import json, math
from dataclasses import dataclass, asdict
from pathlib import Path
import duckdb, numpy as np, pandas as pd

ROOT=Path(__file__).resolve().parents[1]; CACHE=ROOT/"data/cache"; MANIFEST=ROOT/"research/data/ACQUISITION_MANIFEST.json"; OUT=ROOT/"research/results"
OUT.mkdir(parents=True,exist_ok=True)
START="2024-10-01"; END="2025-12-31"; SL=1.0; STOP=100.0
COST={"brokerage_per_order":10.0,"stt_sell_rate":0.001,"exchange_txn_rate":0.0003503,"sebi_rate":0.000001,"ipft_rate":0.000001,"gst_rate":0.18,"stamp_buy_rate":0.00003}

def lot_size(expiry):
 d=pd.Timestamp(expiry).date()
 return 25 if d<=pd.Timestamp("2024-12-26").date() else (75 if d<=pd.Timestamp("2025-12-30").date() else 65)

def fill_cost(raw,side,qty):
 px=raw-SL if side=="SELL" else raw+SL
 tv=abs(px*qty); br=COST["brokerage_per_order"]; stt=tv*COST["stt_sell_rate"] if side=="SELL" else 0
 ex=tv*COST["exchange_txn_rate"]; sebi=tv*COST["sebi_rate"]; ipft=tv*COST["ipft_rate"]
 stamp=tv*COST["stamp_buy_rate"] if side=="BUY" else 0
 gst=COST["gst_rate"]*(br+ex+sebi+ipft)
 return px,dict(brokerage=br,stt=stt,exchange_charge=ex,sebi_fee=sebi,ipft=ipft,stamp_duty=stamp,gst=gst,total_cost=br+stt+ex+sebi+ipft+stamp+gst,slippage_points=SL)

def nearest(x,spot):
 if x.empty:return None
 z=x.dropna(subset=["open"]).copy(); z["d"]=(z.strike-spot).abs()
 return float(z.sort_values(["d","strike"]).iloc[0].strike)

def target(x,premium,spot):
 if x.empty:return None
 z=x.dropna(subset=["open"]).copy(); z["pd"]=(z.open-premium).abs(); z["sd"]=(z.strike-spot).abs()
 return float(z.sort_values(["pd","sd","strike"]).iloc[0].strike)

def px(df,ts,exp,typ,strike,col):
 z=df[(df.timestamp==ts)&(df.expiry==exp)&(df.option_type==typ)&(df.strike==strike)]
 return None if z.empty or pd.isna(z.iloc[0][col]) else float(z.iloc[0][col])

def main():
 m=json.loads(MANIFEST.read_text()); paths=[str(CACHE/"hf_options"/x["source_path"]) for x in m["options_source"]["files"]]
 spot=pd.read_csv(CACHE/"spot/extracted/NIFTY_5min_5yr_2021_2026.csv"); spot.timestamp=pd.to_datetime(spot.timestamp,errors="coerce")
 spot["trade_date"]=spot.timestamp.dt.strftime("%Y-%m-%d")
 s0930=spot[(spot.trade_date.between(START,END))&(spot.timestamp.dt.strftime("%H:%M:%S")=="09:30:00")][["trade_date","close"]].drop_duplicates("trade_date").rename(columns={"close":"spot"})
 con=duckdb.connect(); con.execute("SET TimeZone='Asia/Kolkata'"); con.execute("PRAGMA threads=4")
 fs="["+ ",".join("'"+p.replace("'","''")+"'" for p in paths)+"]"
 con.execute(f"CREATE VIEW options AS SELECT * FROM read_parquet({fs},union_by_name=true)")
 u=con.execute("""WITH e AS(SELECT DISTINCT CAST(date AS DATE) d,CAST(expiry AS DATE)e FROM options WHERE CAST(date AS DATE) BETWEEN DATE '2024-10-01' AND DATE '2025-12-31'),r AS(SELECT d,e,ROW_NUMBER()OVER(PARTITION BY d ORDER BY e)rn FROM e WHERE e>=d)SELECT d,MAX(CASE WHEN rn=1 THEN e END) ce,MAX(CASE WHEN rn=2 THEN e END) ne FROM r GROUP BY d""").df()
 u["trade_date"]=pd.to_datetime(u.d).dt.strftime("%Y-%m-%d"); u=u.drop(columns="d").merge(s0930,on="trade_date"); u["lc"]=u["ce"].map(lot_size); u["ln"]=u["ne"].map(lot_size); u=u[u.lc==u.ln].copy()
 con.register("u",u)
 stage=OUT/"phase4_selected_bars.parquet"
 con.execute(f"""COPY(SELECT CAST(o.date AS DATE) trade_date,o.timestamp,CAST(o.expiry AS DATE) expiry,o.option_type,CAST(o.strike AS DOUBLE) strike,CAST(o.open AS DOUBLE) open,CAST(o.close AS DOUBLE) close FROM options o JOIN u ON CAST(o.date AS DATE)=CAST(u.trade_date AS DATE) AND ((CAST(o.expiry AS DATE)=u.ce AND o.option_type='CE') OR (CAST(o.expiry AS DATE)=u.ne AND o.option_type='PE')) WHERE CAST(o.timestamp AT TIME ZONE 'Asia/Kolkata' AS DATE)=CAST(u.trade_date AS DATE) AND CAST(o.timestamp AT TIME ZONE 'Asia/Kolkata' AS TIME) BETWEEN TIME '09:30:00' AND TIME '15:15:00') TO '{stage.as_posix()}'(FORMAT PARQUET,COMPRESSION ZSTD)""")
 bars=pd.read_parquet(stage); bars.trade_date=pd.to_datetime(bars.trade_date).dt.strftime("%Y-%m-%d"); bars.timestamp=pd.to_datetime(bars.timestamp)
 trades=[]; executions=[]
 for _,r in u.sort_values("trade_date").iterrows():
  d=r.trade_date; df=bars[bars.trade_date==d].copy(); ce=pd.Timestamp(r["ce"]); ne=pd.Timestamp(r["ne"]); lot=int(r["lc"])
  entry=pd.Timestamp(f"{d} 09:30:00",tz="Asia/Kolkata"); exit_ts=pd.Timestamp(f"{d} 15:15:00",tz="Asia/Kolkata")
  a=df[(df.timestamp==entry)&(df.expiry==ce)&(df.option_type=="CE")]; b=df[(df.timestamp==entry)&(df.expiry==ne)&(df.option_type=="PE")]
  ks,ps=nearest(a,r.spot),nearest(b,r.spot)
  if ks is None or ps is None: trades.append({"trade_date":d,"status":"EXCLUDED_UNEXECUTABLE","reason":"missing_entry_contract"}); continue
  cp,pp=px(df,entry,ce,"CE",ks,"open"),px(df,entry,ne,"PE",ps,"open")
  if cp is None or pp is None: trades.append({"trade_date":d,"status":"EXCLUDED_UNEXECUTABLE","reason":"missing_entry_price"}); continue
  legs={"ce":[ce,ks,cp],"pe":[ne,ps,pp]}; realized=0.; stop=False; adj=0; reason="TIME_EXIT"; exs=[]
  for typ,leg in [("ce",legs["ce"]),("pe",legs["pe"])]:
   raw=leg[2]; ep,c=fill_cost(raw,"SELL",lot); exs.append(dict(ts=entry,action="ENTRY",leg=typ,side="SELL",raw=raw,exec=ep,qty=lot,**c)); leg[2]=ep
  times=sorted(df.loc[(df.timestamp>=pd.Timestamp(f"{d} 09:31:00",tz="Asia/Kolkata"))&(df.timestamp<=pd.Timestamp(f"{d} 15:14:00",tz="Asia/Kolkata")),"timestamp"].unique())
  excluded=False
  for ts in times:
   nts=ts+pd.Timedelta(minutes=1)
   marks={}
   for typ,(exp,k,ep) in legs.items():
    v=px(df,ts,exp,"CE" if typ=="ce" else "PE",k,"close")
    if v is not None: marks[typ]=v
   if len(marks)!=2: continue
   pnl=realized+sum(legs[t][2]-marks[t] for t in marks)
   if pnl<=-STOP:
    raws=[px(df,nts,legs[t][0],"CE" if t=="ce" else "PE",legs[t][1],"open") for t in ("ce","pe")]
    if any(v is None for v in raws): excluded=True; reason="UNEXECUTABLE_STOP"; break
    for t,raw in zip(("ce","pe"),raws):
     ep,c=fill_cost(raw,"BUY",lot); exs.append(dict(ts=nts,action="STOP_EXIT",leg=t,side="BUY",raw=raw,exec=ep,qty=lot,**c))
    stop=True; reason="STOP_LOSS"; break
   hi=max(marks.values()); lo=min(marks.values())
   if hi>0 and lo/hi<=.5:
    low=min(marks,key=marks.get); high=max(marks,key=marks.get); exp,k,_=legs[low]
    cand=df[(df.timestamp==nts)&(df.expiry==exp)&(df.option_type==("CE" if low=="ce" else "PE"))]
    nk=target(cand,marks[high],r.spot); old=px(df,nts,exp,"CE" if low=="ce" else "PE",k,"open"); new=px(df,nts,exp,"CE" if low=="ce" else "PE",nk,"open") if nk is not None else None
    if nk is None or old is None or new is None: excluded=True; reason="UNEXECUTABLE_ADJUSTMENT"; break
    ep,c=fill_cost(old,"BUY",lot); exs.append(dict(ts=nts,action="ADJUST_CLOSE",leg=low,side="BUY",raw=old,exec=ep,qty=lot,**c)); realized+=legs[low][2]-ep
    ep2,c2=fill_cost(new,"SELL",lot); exs.append(dict(ts=nts,action="ADJUST_OPEN",leg=low,side="SELL",raw=new,exec=ep2,qty=lot,**c2)); legs[low]=[exp,nk,ep2]; adj+=1
  if excluded: trades.append({"trade_date":d,"status":"EXCLUDED_UNEXECUTABLE","reason":reason,"adjustment_count":adj}); executions.extend(exs); continue
  if not stop:
   raws=[px(df,exit_ts,legs[t][0],"CE" if t=="ce" else "PE",legs[t][1],"open") for t in ("ce","pe")]
   if any(v is None for v in raws): trades.append({"trade_date":d,"status":"EXCLUDED_UNEXECUTABLE","reason":"missing_15_15_exit","adjustment_count":adj}); executions.extend(exs); continue
   for t,raw in zip(("ce","pe"),raws):
    ep,c=fill_cost(raw,"BUY",lot); exs.append(dict(ts=exit_ts,action="TIME_EXIT",leg=t,side="BUY",raw=raw,exec=ep,qty=lot,**c))
  rawp=sum((1 if x["side"]=="SELL" else -1)*x["raw"]*x["qty"] for x in exs); slip=sum(x["slippage_points"]*x["qty"] for x in exs); costs=sum(x["total_cost"] for x in exs)
  trades.append({"trade_date":d,"status":"COMPLETED","exit_reason":reason,"adjustment_count":adj,"stop_hit":stop,"lot_size":lot,"initial_ce_strike":ks,"initial_pe_strike":ps,"gross_pnl_raw":rawp,"slippage_cost":slip,"transaction_costs":costs,"net_pnl":rawp-slip-costs,"order_count":len(exs)})
  executions.extend(exs)
 tr=pd.DataFrame(trades); ex=pd.DataFrame(executions); tr.to_csv(OUT/"trade_ledger.csv",index=False); ex.to_csv(OUT/"execution_ledger.csv",index=False)
 c=tr[tr.status=="COMPLETED"].copy()
 if len(c):
  c["cum"]=c.net_pnl.cumsum(); c["dd"]=c.cum-c.cum.cummax(); pf=c.loc[c.net_pnl>0,"net_pnl"].sum()/abs(c.loc[c.net_pnl<0,"net_pnl"].sum()) if (c.net_pnl<0).any() else math.inf
  summ={"completed_trades":len(c),"excluded_unexecutable":int((tr.status!="COMPLETED").sum()),"total_net_pnl":float(c.net_pnl.sum()),"mean_net_pnl":float(c.net_pnl.mean()),"median_net_pnl":float(c.net_pnl.median()),"win_rate":float((c.net_pnl>0).mean()),"profit_factor":float(pf),"max_drawdown":float(c.dd.min()),"stop_loss_trades":int(c.stop_hit.sum()),"adjustment_trades":int((c.adjustment_count>0).sum()),"total_adjustments":int(c.adjustment_count.sum())}
 else: summ={"completed_trades":0,"excluded_unexecutable":int(len(tr)),"total_net_pnl":None}
 summ.update({"primary_window":{"start":START,"end":END},"cost_model":COST,"slippage_points_per_execution":SL,"reentry":"disabled"})
 (OUT/"primary_backtest_summary.json").write_text(json.dumps(summ,indent=2,default=str)); print(json.dumps(summ,indent=2,default=str))
if __name__=="__main__": main()

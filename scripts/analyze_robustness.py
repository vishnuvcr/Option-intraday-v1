from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
R=ROOT/"research/results"
SPOT=ROOT/"data/cache/spot/extracted/NIFTY_5min_5yr_2021_2026.csv"

def main():
    t=pd.read_csv(R/"trade_ledger.csv")
    t["trade_date"]=pd.to_datetime(t["trade_date"]).dt.normalize()
    t=t.sort_values("trade_date").copy()
    e=pd.read_csv(R/"execution_ledger.csv")
    e["trade_date"]=pd.to_datetime(e["trade_date"]).dt.normalize()
    # Locked cost decomposition: execution total_cost is transaction cost only;
    # slippage is modeled separately as 1 point per executed contract.
    gross=float(t.net_pnl.sum()+t.slippage_cost.sum()+t.transaction_costs.sum())
    tx=float(t.transaction_costs.sum())
    qty=float(e.qty.sum())
    stress=[]
    for slip in [0.0,0.5,1.0,2.0,3.0]:
        net=gross-qty*slip-tx
        stress.append({"slippage_points":slip,"transaction_cost_multiplier":1.0,"net_pnl":net,"return_on_200k":net/200000,"return_on_250k":net/250000})
    for mult in [0.0,0.5,1.0,1.5,2.0]:
        net=gross-float(t.slippage_cost.sum())-tx*mult
        stress.append({"slippage_points":1.0,"transaction_cost_multiplier":mult,"net_pnl":net,"return_on_200k":net/200000,"return_on_250k":net/250000})
    pd.DataFrame(stress).to_csv(R/"ROBUSTNESS_COST_STRESS.csv",index=False)

    # Weekday stratification is pre-specified and descriptive, not selected for tuning.
    t["weekday"]=t.trade_date.dt.day_name()
    wd=t.groupby("weekday",as_index=False).agg(trades=("net_pnl","size"),net_pnl=("net_pnl","sum"),mean_pnl=("net_pnl","mean"),win_rate=("net_pnl",lambda x:float((x>0).mean())))
    wd.to_csv(R/"ROBUSTNESS_WEEKDAY.csv",index=False)

    # Contract-lot regime stratification is fixed by the historical contract schedule.
    lr=t.groupby("lot_size",as_index=False).agg(trades=("net_pnl","size"),net_pnl=("net_pnl","sum"),mean_pnl=("net_pnl","mean"),win_rate=("net_pnl",lambda x:float((x>0).mean())))
    lr.to_csv(R/"ROBUSTNESS_LOT_REGIME.csv",index=False)

    # Market-regime proxy: 20-trading-day realized volatility of the 09:30 NIFTY close,
    # split at the sample median. This rule is frozen before looking at P&L.
    spot=pd.read_csv(SPOT)
    spot["timestamp"]=pd.to_datetime(spot["timestamp"],errors="coerce")
    spot=spot.dropna(subset=["timestamp"]).sort_values("timestamp")
    s=spot[(spot.timestamp.dt.time==pd.Timestamp("09:30").time())][["timestamp","close"]].copy()
    s["trade_date"]=s.timestamp.dt.normalize()
    s=s.drop_duplicates("trade_date").sort_values("trade_date")
    s["ret"]=s.close.pct_change()
    s["rv20"]=s.ret.rolling(20,min_periods=20).std()*np.sqrt(252)
    s=s[["trade_date","rv20"]]
    t=t.merge(s,on="trade_date",how="left")
    cut=float(t["rv20"].median())
    t["vol_regime"]=np.where(t["rv20"].isna(),"UNCLASSIFIED",np.where(t["rv20"]<=cut,"LOW_VOL","HIGH_VOL"))
    vr=t[t.vol_regime!="UNCLASSIFIED"].groupby("vol_regime",as_index=False).agg(trades=("net_pnl","size"),net_pnl=("net_pnl","sum"),mean_pnl=("net_pnl","mean"),win_rate=("net_pnl",lambda x:float((x>0).mean())))
    vr.to_csv(R/"ROBUSTNESS_VOLATILITY_REGIME.csv",index=False)

    result={
      "sample_trades":int(len(t)),
      "pre_specified_rules":{
        "slippage_grid_points":[0,0.5,1,2,3],
        "transaction_cost_multiplier_grid":[0,0.5,1,1.5,2],
        "weekday_stratification":"calendar weekday",
        "lot_regime":"historical lot size attached to trade",
        "volatility_regime":"20-trading-day 09:30 spot return realized volatility, split at sample median"
      },
      "volatility_median_cut":cut,
      "unclassified_volatility_trades":int((t.vol_regime=="UNCLASSIFIED").sum()),
      "primary_rule_changed":False,
      "optimization_performed":False,
      "status":"phase6_robustness_complete; tester_gate_pending"
    }
    (R/"ROBUSTNESS_SUMMARY.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2))

if __name__=="__main__":main()

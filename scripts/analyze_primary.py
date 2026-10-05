from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import skew, kurtosis

ROOT=Path(__file__).resolve().parents[1]
R=ROOT/"research/results"
OUT=R
BOOT=10000
CAPITALS=[200000.0,250000.0]

def bootstrap_ci(x, seed=20261005):
    rng=np.random.default_rng(seed)
    x=np.asarray(x,dtype=float)
    if len(x)==0:return [None,None]
    means=np.empty(BOOT)
    for i in range(BOOT):
        means[i]=rng.choice(x,size=len(x),replace=True).mean()
    return [float(np.quantile(means,.025)),float(np.quantile(means,.975))]

def main():
    t=pd.read_csv(R/"trade_ledger.csv")
    t=t[t["status"]=="COMPLETED"].copy()
    t["trade_date"]=pd.to_datetime(t["trade_date"])
    t=t.sort_values("trade_date")
    x=t["net_pnl"].astype(float)
    daily=t.groupby("trade_date",as_index=False)["net_pnl"].sum()
    dr=daily["net_pnl"]/CAPITALS[0]
    sharpe=float(dr.mean()/dr.std(ddof=1)*np.sqrt(252)) if dr.std(ddof=1)>0 else None
    downside=dr[dr<0].std(ddof=1)
    sortino=float(dr.mean()/downside*np.sqrt(252)) if downside and downside>0 else None
    var5=float(np.quantile(x,.05))
    es5=float(x[x<=var5].mean())
    summary=json.loads((R/"primary_backtest_summary.json").read_text())
    summary["workflow_run_id"]=37252528338
    summary["status"]="phase5_primary_run_complete; tester_gate_pending"
    summary.update({
        "bootstrap_mean_net_pnl_ci_95":bootstrap_ci(x),
        "trade_pnl_skewness":float(skew(x,bias=False)) if len(x)>2 else None,
        "trade_pnl_excess_kurtosis":float(kurtosis(x,bias=False)) if len(x)>3 else None,
        "trade_pnl_var_5pct":var5,
        "trade_pnl_expected_shortfall_5pct":es5,
        "daily_sharpe_annualized_on_200k":sharpe,
        "daily_sortino_annualized_on_200k":sortino,
        "return_on_200k":float(x.sum()/200000),
        "return_on_250k":float(x.sum()/250000),
        "average_daily_net_pnl":float(daily.net_pnl.mean()),
        "daily_net_pnl_std":float(daily.net_pnl.std(ddof=1)),
        "worst_trade":float(x.min()),
        "best_trade":float(x.max()),
    })
    (OUT/"PRIMARY_STATISTICS.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    monthly=t.assign(month=t.trade_date.dt.to_period("M").astype(str)).groupby("month",as_index=False).agg(
        trades=("net_pnl","size"),net_pnl=("net_pnl","sum"),mean_pnl=("net_pnl","mean"),
        win_rate=("net_pnl",lambda z:float((z>0).mean())))
    monthly.to_csv(OUT/"PRIMARY_MONTHLY_RESULTS.csv",index=False)
    events=t.groupby(t.trade_date.dt.to_period("M").astype(str),as_index=False).agg(
        trades=("net_pnl","size"),stop_loss_trades=("stop_hit","sum"),
        adjustment_trades=("adjustment_count",lambda z:int((z>0).sum())),
        total_adjustments=("adjustment_count","sum"))
    events.to_csv(OUT/"PRIMARY_EVENT_COUNTS_MONTHLY.csv",index=False)
    # Charts are intentionally descriptive and generated from frozen primary results.
    import matplotlib.pyplot as plt
    plt.figure(figsize=(10,5)); plt.plot(t.trade_date,t.net_pnl.cumsum()); plt.axhline(0); plt.title("Primary cumulative net P&L"); plt.xlabel("Date"); plt.ylabel("INR"); plt.tight_layout(); plt.savefig(OUT/"primary_equity_curve.png",dpi=160); plt.close()
    cum=t.net_pnl.cumsum(); dd=cum-cum.cummax()
    plt.figure(figsize=(10,4)); plt.plot(t.trade_date,dd); plt.axhline(0); plt.title("Primary drawdown"); plt.xlabel("Date"); plt.ylabel("INR"); plt.tight_layout(); plt.savefig(OUT/"primary_drawdown.png",dpi=160); plt.close()
    plt.figure(figsize=(8,5)); plt.hist(t.net_pnl,bins=40); plt.axvline(0); plt.title("Trade-level net P&L distribution"); plt.xlabel("INR"); plt.ylabel("Trades"); plt.tight_layout(); plt.savefig(OUT/"primary_pnl_distribution.png",dpi=160); plt.close()
    print(json.dumps(summary,indent=2))

if __name__=="__main__":main()

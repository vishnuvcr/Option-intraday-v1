from __future__ import annotations
import json
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
R=ROOT/"research/results"
CUT=pd.Timestamp("2025-07-01")

def metrics(t):
    x=t.net_pnl.astype(float)
    gross=t.gross_pnl_raw.sum(); slip=t.slippage_cost.sum(); tx=t.transaction_costs.sum()
    return {
      "trades":int(len(t)),
      "net_pnl":float(x.sum()),
      "gross_pnl":float(gross),
      "slippage":float(slip),
      "transaction_costs":float(tx),
      "mean_pnl":float(x.mean()),
      "median_pnl":float(x.median()),
      "win_rate":float((x>0).mean()),
      "profit_factor":float(x[x>0].sum()/abs(x[x<0].sum())) if (x<0).any() else None,
      "max_drawdown":float((x.cumsum()-x.cumsum().cummax()).min()),
      "stop_loss_trades":int(t.stop_hit.sum()),
      "adjustment_trades":int((t.adjustment_count>0).sum()),
      "total_adjustments":int(t.adjustment_count.sum()),
    }

def main():
    t=pd.read_csv(R/"trade_ledger.csv")
    t["trade_date"]=pd.to_datetime(t.trade_date)
    dev=t[t.trade_date<CUT].copy()
    forward=t[t.trade_date>=CUT].copy()
    out={
      "cutoff":"2025-07-01",
      "development_slice":metrics(dev),
      "forward_slice":metrics(forward),
      "forward_slice_is_prospective":False,
      "reason_not_prospective":"The primary backtest was run across the full validated 2024-10-01 to 2025-12-31 sample before this split was formalized; therefore this is a chronological diagnostic, not a prospectively sequestered OOS test.",
      "parameters_changed":False,
      "cost_model_unchanged":True,
      "status":"phase8_forward_diagnostic_complete; tester_gate_pending"
    }
    # Forward-slice cost stress, using frozen execution-derived costs.
    gross=float(forward.gross_pnl_raw.sum()); tx=float(forward.transaction_costs.sum()); qty=float(forward.order_count.mul(forward.lot_size).sum())
    rows=[]
    for slip in [0,0.5,1,2]:
        net=gross-qty*slip-tx
        rows.append({"slippage_points":slip,"net_pnl":net,"return_on_200k":net/200000,"return_on_250k":net/250000})
    pd.DataFrame(rows).to_csv(R/"OOS_FORWARD_COST_STRESS.csv",index=False)
    (R/"OOS_FORWARD_DIAGNOSTIC.json").write_text(json.dumps(out,indent=2),encoding="utf-8")
    print(json.dumps(out,indent=2))

if __name__=="__main__":main()

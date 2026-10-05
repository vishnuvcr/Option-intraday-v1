from __future__ import annotations
import json
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
R=ROOT/"research/results"

def main():
    t=pd.read_csv(R/"trade_ledger.csv")
    e=pd.read_csv(R/"execution_ledger.csv")
    expected=json.loads((R/"PRIMARY_BACKTEST_SUMMARY.json").read_text())
    checks={
      "trade_count":int(len(t)),
      "completed_count":int((t.status=="COMPLETED").sum()),
      "net_pnl":float(t.net_pnl.sum()),
      "gross_pnl":float(t.gross_pnl_raw.sum()),
      "slippage":float(t.slippage_cost.sum()),
      "transaction_costs":float(t.transaction_costs.sum()),
      "win_rate":float((t.net_pnl>0).mean()),
      "max_drawdown":float((t.net_pnl.cumsum()-t.net_pnl.cumsum().cummax()).min()),
      "stop_loss_trades":int(t.stop_hit.sum()),
      "adjustment_trades":int((t.adjustment_count>0).sum()),
      "total_adjustments":int(t.adjustment_count.sum()),
      "execution_rows":int(len(e)),
      "execution_qty":float(e.qty.sum()),
      "execution_cost_sum":float(e.total_cost.sum()),
      "execution_slippage_points_sum":float(e.slippage_points.sum()),
    }
    checks["reconciliation_net"]=checks["gross_pnl"]-checks["slippage"]-checks["transaction_costs"]
    comparisons={
      "trade_count":checks["trade_count"]==expected["completed_trades"],
      "net_pnl":abs(checks["net_pnl"]-expected["total_net_pnl_inr"])<1e-6,
      "gross_pnl":abs(checks["gross_pnl"]-expected["total_gross_pnl_raw_inr"])<1e-6,
      "slippage":abs(checks["slippage"]-expected["total_slippage_cost_inr"])<1e-6,
      "transaction_costs":abs(checks["transaction_costs"]-expected["total_transaction_costs_inr"])<1e-6,
      "win_rate":abs(checks["win_rate"]-expected["win_rate"])<1e-12,
      "max_drawdown":abs(checks["max_drawdown"]-expected["max_drawdown_inr"])<1e-6,
      "stop_loss_trades":checks["stop_loss_trades"]==expected["stop_loss_trades"],
      "adjustment_trades":checks["adjustment_trades"]==expected["adjustment_trades"],
      "total_adjustments":checks["total_adjustments"]==expected["total_adjustments"],
      "execution_cost_sum":abs(checks["execution_cost_sum"]-expected["total_transaction_costs_inr"])<1e-6,
      "execution_slippage_qty":abs(checks["execution_qty"]-expected["total_slippage_cost_inr"])<1e-6,
    }
    out={"checks":checks,"comparisons":comparisons,"all_pass":all(comparisons.values()),"status":"phase7_audit_complete"}
    (R/"INDEPENDENT_AUDIT.json").write_text(json.dumps(out,indent=2),encoding="utf-8")
    if not out["all_pass"]: raise SystemExit(json.dumps(out,indent=2))
    print(json.dumps(out,indent=2))

if __name__=="__main__":main()

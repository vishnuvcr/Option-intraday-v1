import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from scripts.backtest_engine import (
    allow_adjustment,
    asof_spot,
    fill_cost,
    lot_size,
    nearest,
    ratio_trigger,
    should_stop,
    short_pnl_points,
    target,
)


def test_lot_regimes():
    assert lot_size(pd.Timestamp("2024-12-26")) == 25
    assert lot_size(pd.Timestamp("2025-01-02")) == 75
    assert lot_size(pd.Timestamp("2025-12-30")) == 75
    assert lot_size(pd.Timestamp("2025-12-31")) == 65


def test_nearest_tie_lower():
    frame = pd.DataFrame({"strike": [100.0, 110.0], "open": [5.0, 5.0]})
    assert nearest(frame, 105.0) == 100.0


def test_adjustment_target_tie_break():
    frame = pd.DataFrame({
        "strike": [90.0, 100.0, 110.0],
        "open": [21.0, 19.5, 20.5],
    })
    assert target(frame, 20.0, 100.0) == 100.0


def test_slippage_direction():
    sell, sell_cost = fill_cost(10.0, "SELL", 25)
    buy, buy_cost = fill_cost(10.0, "BUY", 25)
    assert sell == 9.0
    assert buy == 11.0
    assert sell_cost["slippage_points"] == 1.0
    assert buy_cost["slippage_points"] == 1.0


def test_cost_components():
    _, costs = fill_cost(100.0, "SELL", 25)
    turnover = 99.0 * 25
    assert abs(costs["exchange_charge"] - turnover * 0.0003503) < 1e-12
    assert abs(costs["ipft"] - turnover * 0.000005) < 1e-12
    assert abs((costs["exchange_charge"] + costs["ipft"]) - turnover * 0.0003553) < 1e-12
    assert costs["stamp_duty"] == 0.0


def test_stop_is_based_on_raw_market_points():
    legs = {
        "ce": {"raw_entry": 60.0},
        "pe": {"raw_entry": 60.0},
    }
    marks = {"ce": 120.0, "pe": 100.0}
    pnl = short_pnl_points(0.0, legs, marks)
    assert pnl == -100.0
    assert should_stop(pnl, 100.0)


def test_stop_not_triggered_above_threshold():
    legs = {
        "ce": {"raw_entry": 60.0},
        "pe": {"raw_entry": 60.0},
    }
    marks = {"ce": 110.0, "pe": 100.0}
    assert short_pnl_points(0.0, legs, marks) == -90.0
    assert not should_stop(-90.0, 100.0)


def test_ratio_trigger_direction():
    assert ratio_trigger(20.0, 40.0)
    assert ratio_trigger(40.0, 20.0)
    assert not ratio_trigger(20.1, 40.0)


def test_no_adjustment_at_15_15_exit():
    t = pd.Timestamp("2025-01-02 15:15:00")
    assert not allow_adjustment(t, t)


def test_adjustment_allowed_before_exit():
    t = pd.Timestamp("2025-01-02 15:14:00")
    x = pd.Timestamp("2025-01-02 15:15:00")
    assert allow_adjustment(t, x)


def test_point_in_time_spot_tie_break_has_no_future_lookahead():
    spot = pd.DataFrame({
        "timestamp": pd.to_datetime([
            "2025-01-02 09:30:00",
            "2025-01-02 09:35:00",
            "2025-01-02 09:40:00",
        ]),
        "close": [100.0, 105.0, 200.0],
    })
    assert asof_spot(spot, pd.Timestamp("2025-01-02 09:34:00")) == 100.0


def test_zero_price_sell_is_floored_at_zero():
    price, _ = fill_cost(0.5, "SELL", 25)
    assert price == 0.0


def test_realized_roll_is_already_in_option_points():
    legs={"ce":{"raw_entry":60.0},"pe":{"raw_entry":60.0}}
    marks={"ce":100.0,"pe":80.0}
    assert short_pnl_points(20.0, legs, marks) == -60.0

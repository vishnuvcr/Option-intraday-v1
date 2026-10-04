import pandas as pd
from scripts.backtest_engine import lot_size, nearest, target, fill_cost

def test_lot_regimes():
    assert lot_size(pd.Timestamp('2024-12-26')) == 25
    assert lot_size(pd.Timestamp('2025-01-02')) == 75
    assert lot_size(pd.Timestamp('2025-12-30')) == 75
    assert lot_size(pd.Timestamp('2025-12-31')) == 65

def test_nearest_tie_lower():
    df=pd.DataFrame({'strike':[100.0,110.0],'open':[5.0,5.0]})
    assert nearest(df,105.0)==100.0

def test_adjustment_target():
    df=pd.DataFrame({'strike':[90.0,100.0,110.0],'open':[21.0,19.5,20.5]})
    assert target(df,20.0,100.0)==90.0

def test_slippage_direction():
    sell,_=fill_cost(10.0,'SELL',25); buy,_=fill_cost(10.0,'BUY',25)
    assert sell==9.0 and buy==11.0

def test_cost_components():
    _,c=fill_cost(10.0,'SELL',25)
    assert all(k in c for k in ['brokerage','stt','exchange_charge','sebi_fee','ipft','stamp_duty','gst','total_cost'])

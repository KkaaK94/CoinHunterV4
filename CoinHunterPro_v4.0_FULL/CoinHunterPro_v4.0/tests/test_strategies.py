# tests/test_strategies.py

import pytest
import pandas as pd
from strategies.rsi import RsiStrategy
from strategies.macd import MacdStrategy
from strategies.ma_cross import MaCrossStrategy

@pytest.fixture
def price_data():
    # 단순한 우상향 시계열 데이터 생성
    return pd.Series([i for i in range(1, 51)])

def test_rsi_strategy(price_data):
    strategy = RsiStrategy(params={
        "entry_threshold": 30,
        "exit_threshold": 70,
        "period": 14
    })
    ticker = "KRW-BTC"
    strategy.init_state(ticker)

    for price in price_data:
        strategy.update_price_series(ticker, price)  # 내부 상태 업데이트

    assert isinstance(strategy.should_enter(ticker, price_data.iloc[-1]), bool)
    assert isinstance(strategy.should_exit(ticker, price_data.iloc[-1]), bool)

def test_macd_strategy(price_data):
    strategy = MacdStrategy(
    params={
        "short_window": 12,
        "long_window": 26,
        "signal_window": 9
    }
)
    ticker = "KRW-ETH"
    strategy.init_state(ticker)

    for price in price_data:
        strategy.update_price_series(ticker, price)

    assert isinstance(strategy.should_enter(ticker, price_data.iloc[-1]), bool)
    assert isinstance(strategy.should_exit(ticker, price_data.iloc[-1]), bool)

def test_ma_cross_strategy(price_data):
    strategy = MaCrossStrategy({
        "short_window": 5,
        "long_window": 20
    })
    ticker = "KRW-XRP"
    strategy.init_state(ticker)

    for price in price_data:
        strategy.update_price_series(ticker, price)

    assert isinstance(strategy.should_enter(ticker, price_data.iloc[-1]), bool)
    assert isinstance(strategy.should_exit(ticker, price_data.iloc[-1]), bool)

# strategies/ma_cross.py

import numpy as np
import pandas as pd
from datetime import datetime
from strategies.base_strategy import BaseStrategy
from utils.logger import log_message, log_to_trade_json

class MaCrossStrategy(BaseStrategy):
    name = "MA_CROSS"

    def __init__(self, params):
        super().__init__(params)
        self.short = params.get("short_window", 5)
        self.long = params.get("long_window", 20)
        self.amount_precision = params.get("amount_precision", 6)

        self.entry_count = 0
        self.exit_count = 0
        self.cumulative_pnl = 0
        self.holding_periods = []

        self.market_state = {}

    def update_price_series(self, ticker, price):
        self.init_state(ticker)
        series = self.state[ticker]["price_series"]

        if series.empty:
            series = pd.Series([price])
        else:
            series = pd.concat([series, pd.Series([price])], ignore_index=True)

        if len(series) > 100:
            series = series[-100:]
        self.state[ticker]["price_series"] = series

    def _calculate_ma(self, series):
        short_ma = series.rolling(self.short).mean()
        long_ma = series.rolling(self.long).mean()
        return short_ma, long_ma

    def _tag_market_state(self, series):
        trend = "up" if series.diff().mean() > 0 else "down"
        volatility = "high" if series.std() > series.mean() * 0.01 else "low"
        return trend, volatility

    def should_enter(self, ticker, current_price):
        self.update_price_series(ticker, current_price)
        series = self.state[ticker]["price_series"]

        if len(series) < self.long:
            return False

        short_ma, long_ma = self._calculate_ma(series)
        trend, volatility = self._tag_market_state(series)
        self.market_state[ticker] = {"trend": trend, "volatility": volatility}

        if short_ma.iloc[-1] > long_ma.iloc[-1] and short_ma.iloc[-2] <= long_ma.iloc[-2]:
            self.entry_count += 1
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_message(f"[진입] {ticker} 교차 진입 / 가격: {current_price}")
            log_to_trade_json(ticker, {
                "event": "entry",
                "time": now,
                "price": current_price,
                "strategy": self.name,
                "market_state": self.market_state[ticker],
                "entry_count": self.entry_count
            })
            self.state[ticker]["last_entry_time"] = datetime.now()
            return True
        return False

    def should_exit(self, ticker, current_price):
        series = self.state[ticker]["price_series"]
        short_ma, long_ma = self._calculate_ma(series)

        if short_ma.iloc[-1] < long_ma.iloc[-1] and short_ma.iloc[-2] >= long_ma.iloc[-2]:
            self.exit_count += 1
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_message(f"[청산] {ticker} 교차 청산 / 가격: {current_price}")
            log_to_trade_json(ticker, {
                "event": "exit",
                "time": now,
                "price": current_price,
                "strategy": self.name,
                "market_state": self.market_state.get(ticker, {}),
                "exit_count": self.exit_count
            })

            if "last_entry_time" in self.state[ticker]:
                duration = (datetime.now() - self.state[ticker]["last_entry_time"]).total_seconds()
                self.holding_periods.append(duration)

            return True
        return False

    def get_statistics(self):
        if self.holding_periods:
            return {
                "strategy": self.name,
                "entry_count": self.entry_count,
                "exit_count": self.exit_count,
                "avg_holding_period": np.mean(self.holding_periods),
                "std_holding_period": np.std(self.holding_periods),
                "cumulative_pnl": self.cumulative_pnl
            }
        return {}

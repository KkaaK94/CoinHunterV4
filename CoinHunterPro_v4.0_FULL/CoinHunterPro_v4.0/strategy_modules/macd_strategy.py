# strategies/macd.py
import pandas as pd
import numpy as np
from utils.logger import log_message, log_to_trade_json
from strategies.base_strategy import BaseStrategy
from datetime import datetime

class MacdStrategy(BaseStrategy):
    name = "MACD"

    def __init__(self, params, capital=1000000, precision=6):
        super().__init__(params, capital, precision)
        self.params = params
        self.entry_count = 0
        self.exit_count = 0
        self.cumulative_pnl = 0.0
        self.entry_times = {}

    def init_state(self, ticker):
        if ticker not in self.state:
            self.state[ticker] = {
                "macd_history": [],
                "signal_history": [],
                "last_signal": None,
                "price_series": pd.Series(dtype=float)
            }

    def update_price_series(self, ticker, price):
        self.init_state(ticker)
        ps = self.state[ticker]["price_series"]
        if ps.empty:
            self.state[ticker]["price_series"] = pd.Series([price])
        else:
            self.state[ticker]["price_series"] = pd.concat([ps, pd.Series([price])], ignore_index=True)
        if len(self.state[ticker]["price_series"]) > 100:
            self.state[ticker]["price_series"] = self.state[ticker]["price_series"].iloc[-100:]

    def update_macd_series(self, ticker, price_series: pd.Series):
        if len(price_series) < max(self.params["short_window"], self.params["long_window"]) + 1:
            self.state[ticker]["macd"] = np.nan
            self.state[ticker]["signal"] = np.nan
            return

        ema_short = price_series.ewm(span=self.params["short_window"], adjust=False).mean()
        ema_long = price_series.ewm(span=self.params["long_window"], adjust=False).mean()
        macd_line = ema_short - ema_long
        signal_line = macd_line.ewm(span=self.params["signal_window"], adjust=False).mean()

        self.state[ticker]["macd"] = macd_line.iloc[-1]
        self.state[ticker]["signal"] = signal_line.iloc[-1]
        self.state[ticker]["macd_history"].append(self.state[ticker]["macd"])
        self.state[ticker]["signal_history"].append(self.state[ticker]["signal"])

    def should_enter(self, ticker, current_price: float) -> bool:
        self.update_price_series(ticker, current_price)
        self.update_macd_series(ticker, self.state[ticker]["price_series"])
        macd = self.state[ticker]["macd"]
        signal = self.state[ticker]["signal"]
        if np.isnan(macd) or np.isnan(signal):
            return False
        if macd > signal and self.state[ticker]["last_signal"] != "entry":
            self.state[ticker]["last_signal"] = "entry"
            self.entry_count += 1
            self.entry_times[ticker] = datetime.now()
            log_message(f"[진입신호] {self.log_prefix(ticker)} MACD > Signal")
            log_to_trade_json(ticker, {
                "event": "entry_signal",
                "macd": macd,
                "signal": signal,
                "entry_price": current_price,
                "strategy": self.name
            })
            return True
        return False

    def should_exit(self, ticker, current_price: float) -> bool:
        self.update_price_series(ticker, current_price)
        self.update_macd_series(ticker, self.state[ticker]["price_series"])
        macd = self.state[ticker]["macd"]
        signal = self.state[ticker]["signal"]
        if np.isnan(macd) or np.isnan(signal):
            return False
        if macd < signal and self.state[ticker]["last_signal"] != "exit":
            self.state[ticker]["last_signal"] = "exit"
            self.exit_count += 1
            exit_time = datetime.now()
            entry_time = self.entry_times.get(ticker)
            holding_period = (exit_time - entry_time).seconds if entry_time else None
            log_message(f"[청산신호] {self.log_prefix(ticker)} MACD < Signal / 보유기간: {holding_period}초")
            log_to_trade_json(ticker, {
                "event": "exit_signal",
                "macd": macd,
                "signal": signal,
                "exit_price": current_price,
                "strategy": self.name,
                "holding_period_sec": holding_period
            })
            return True
        return False

    def update_pnl(self, pnl: float):
        self.cumulative_pnl += pnl

    def describe(self):
        return {
            "strategy": self.name,
            "params": self.params,
            "entries": self.entry_count,
            "exits": self.exit_count,
            "pnl": round(self.cumulative_pnl, 2)
        }

    def reset_state(self):
        self.state = {}
        self.entry_count = 0
        self.exit_count = 0
        self.cumulative_pnl = 0.0
        self.entry_times = {}

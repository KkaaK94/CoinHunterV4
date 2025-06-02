# strategies/rsi.py

import pandas as pd
import numpy as np
import json
import os
from strategies.base_strategy import BaseStrategy
from utils.logger import log_to_trade_json


class RsiStrategy(BaseStrategy):
    def __init__(self, name="RSI", capital_dict=None, params=None, amount_precision=6):
        if capital_dict is None:
            capital_dict = {}
        if params is None:
            params = {"entry_threshold": 30, "exit_threshold": 70, "period": 14}
        super().__init__(name, capital_dict, params, amount_precision)

        # 추가 상태값
        self.rsi_cache = {}
        self.entry_count = {}
        self.exit_count = {}
        self.rsi_history = {}

    def _calculate_rsi(self, ticker, price):
        if ticker not in self.state:
            self.state[ticker] = {"closes": [], "last_signal": None, "rsi": None}
            self.rsi_history[ticker] = []

        self.state[ticker]["closes"].append(price)
        closes = self.state[ticker]["closes"]

        period = self.params["period"]
        if len(closes) < period + 1:
            return None

        series = pd.Series(closes[-(period + 1):])
        delta = series.diff()
        up = delta.clip(lower=0).mean()
        down = -delta.clip(upper=0).mean()
        rs = up / down if down != 0 else np.inf
        rsi = 100 - (100 / (1 + rs))

        if np.isnan(rsi):
            return None

        self.rsi_cache[ticker] = rsi
        self.state[ticker]["rsi"] = rsi
        self.rsi_history[ticker].append(rsi)
        return rsi

    def should_enter(self, ticker, current_price):
        rsi = self._calculate_rsi(ticker, current_price)
        if rsi is None:
            return False

        if rsi < self.params["entry_threshold"]:
            self.state[ticker]["last_signal"] = "entry"
            self.entry_count[ticker] = self.entry_count.get(ticker, 0) + 1

            print(f"{self.log_prefix(ticker)} 진입 조건 만족 (RSI={rsi:.2f})")
            log_to_trade_json(ticker, {
                "action": "entry",
                "price": current_price,
                "rsi": rsi,
                "entry_count": self.entry_count[ticker],
                "strategy": self.name
            })
            return True

        print(f"{self.log_prefix(ticker)} 진입 조건 불충족 (RSI={rsi:.2f})")
        return False

    def should_exit(self, ticker, current_price):
        rsi = self._calculate_rsi(ticker, current_price)
        if rsi is None:
            return False

        if rsi > self.params["exit_threshold"]:
            self.state[ticker]["last_signal"] = "exit"
            self.exit_count[ticker] = self.exit_count.get(ticker, 0) + 1

            print(f"{self.log_prefix(ticker)} 청산 조건 만족 (RSI={rsi:.2f})")
            log_to_trade_json(ticker, {
                "action": "exit",
                "price": current_price,
                "rsi": rsi,
                "exit_count": self.exit_count[ticker],
                "strategy": self.name
            })
            return True

        print(f"{self.log_prefix(ticker)} 청산 조건 불충족 (RSI={rsi:.2f})")
        return False

    def get_latest_rsi(self, ticker):
        return self.state.get(ticker, {}).get("rsi")

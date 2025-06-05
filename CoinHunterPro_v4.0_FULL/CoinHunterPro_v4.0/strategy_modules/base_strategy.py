# strategies/base_strategy.py

from abc import ABC, abstractmethod
import pandas as pd

class BaseStrategy(ABC):
    def __init__(self, params=None, capital=1000000, precision=6):
        self.params = params or {}
        self.capital = capital
        self.precision = precision
        self.prices = {}  # 실시간 가격 기록용
        self.state = {}   # 전략 상태 초기화 저장용

    def update_price(self, ticker, price):
        """티커별 현재가 업데이트"""
        self.prices[ticker] = price

    def get_price(self, ticker):
        """티커별 현재가 조회 (없으면 0)"""
        return self.prices.get(ticker, 0)

    def log_prefix(self, ticker):
        """[전략명][티커] 형식 로그 prefix"""
        return f"[{getattr(self, 'name', 'Strategy')}][{ticker}]"

    def describe(self):
        """전략 파라미터 요약 출력"""
        print(f"\n📊 전략명: {getattr(self, 'name', 'Strategy')}")
        print(f"🧮 파라미터: {self.params}")
        print(f"💰 초기 자본: {self.capital}")
        print(f"🔢 수량 정밀도: {self.precision}")

    def reset_state(self, ticker=None):
        """전략별 상태 초기화"""
        if ticker:
            self.state[ticker] = {}
        else:
            self.state = {}

    def init_state(self, ticker):
        """MACD 등 price_series 기반 전략에서 필요한 초기 상태 세팅"""
        if ticker not in self.state:
            self.state[ticker] = {"price_series": pd.Series(dtype=float)}

    @abstractmethod
    def should_enter(self, ticker, current_price):
        """진입 조건 판단 로직"""
        pass

    @abstractmethod
    def should_exit(self, ticker, current_price):
        """청산 조건 판단 로직"""
        pass

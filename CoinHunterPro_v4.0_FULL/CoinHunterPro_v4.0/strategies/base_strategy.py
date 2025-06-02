# strategies/base_strategy.py

from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    def __init__(self, name, capital_dict, params, amount_precision=6):
        """
        :param name: 전략 이름 (예: "RSI")
        :param capital_dict: {"KRW-BTC": 10000, "KRW-ETH": 5000} 등
        :param params: 전략별 파라미터 dict
        :param amount_precision: 수량 소수점 자리수
        """
        self.name = name
        self.capital_dict = capital_dict
        self.params = params
        self.amount_precision = amount_precision
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
        return f"[{self.name}][{ticker}]"

    def describe(self):
        """전략 파라미터 요약 출력"""
        print(f"\n📊 전략명: {self.name}")
        print(f"🧮 파라미터: {self.params}")
        print(f"💰 자본 분배: {self.capital_dict}")
        print(f"🔢 수량 정밀도: {self.amount_precision}")

    def reset_state(self, ticker=None):
        """전략별 상태 초기화"""
        if ticker:
            self.state[ticker] = {}
        else:
            self.state = {}

    @abstractmethod
    def should_enter(self, ticker, current_price):
        """진입 조건 판단 로직"""
        pass

    @abstractmethod
    def should_exit(self, ticker, current_price):
        """청산 조건 판단 로직"""
        pass

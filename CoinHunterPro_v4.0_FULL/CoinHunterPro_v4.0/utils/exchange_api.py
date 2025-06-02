# utils/exchange_api.py

import pyupbit
import os
import time
from security.env_config import get_api_keys
from utils.logger import log_to_trade_json


class ExchangeAPI:
    def __init__(self, is_live=False, slippage=0.001, fee=0.0005, max_retry=3):
        self.is_live = is_live
        self.slippage = slippage
        self.fee = fee
        self.max_retry = max_retry

        if self.is_live:
            keys = get_api_keys()
            self.upbit = pyupbit.Upbit(keys['UPBIT_ACCESS_KEY'], keys['UPBIT_SECRET_KEY'])

    def get_current_price(self, ticker):
        try:
            price = pyupbit.get_current_price(ticker)
            return price if price else 0
        except Exception as e:
            print(f"[API 오류] {ticker} 가격 조회 실패: {e}")
            return 0

    def get_balance(self, ticker="KRW"):
        if self.is_live:
            try:
                return self.upbit.get_balance(ticker)
            except Exception as e:
                print(f"[API 오류] 잔고 조회 실패: {e}")
                return 0
        return 1_000_000_000  # 페이퍼 트레이딩 모드 기본 자본

    def place_order(self, ticker, side, amount):
        for attempt in range(self.max_retry):
            try:
                if self.is_live:
                    if side == "buy":
                        order = self.upbit.buy_market_order(ticker, amount)
                    elif side == "sell":
                        order = self.upbit.sell_market_order(ticker, amount)
                    else:
                        raise ValueError("Unknown order side")

                    log_to_trade_json(ticker, {
                        "side": side,
                        "amount": amount,
                        "price": self.get_current_price(ticker),
                        "mode": "LIVE",
                        "order": order
                    })
                    return order
                else:
                    # 페이퍼 트레이딩: 가격 슬리피지 및 수수료 적용
                    market_price = self.get_current_price(ticker)
                    price = market_price * (1 + self.slippage if side == "buy" else 1 - self.slippage)
                    net_price = price * (1 - self.fee)

                    log_to_trade_json(ticker, {
                        "side": side,
                        "amount": amount,
                        "price": net_price,
                        "mode": "PAPER",
                        "slippage": self.slippage,
                        "fee": self.fee
                    })
                    print(f"[모의주문] {ticker} {side.upper()} @ {net_price:.0f} x {amount}")
                    return {"result": "success", "side": side, "price": net_price, "amount": amount}

            except Exception as e:
                print(f"[주문 재시도 {attempt+1}/{self.max_retry}] 실패: {e}")
                time.sleep(1)

        print(f"[최종실패] {ticker} 주문 실패")
        return {"result": "error", "message": "주문 실패"}

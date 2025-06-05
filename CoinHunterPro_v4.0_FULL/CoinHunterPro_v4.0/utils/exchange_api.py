# utils/exchange_api.py

import os
import time
import pyupbit
from dotenv import load_dotenv
from loguru import logger
from utils.push_notification import send_alert
from utils.json_manager import load_json

# ✅ 환경 변수 로드 (.env)
load_dotenv()
ACCESS_KEY = os.getenv("UPBIT_ACCESS_KEY")
SECRET_KEY = os.getenv("UPBIT_SECRET_KEY")
ENABLE_ALERTS = os.getenv("ENABLE_ALERTS", "false").lower() == "true"

# ✅ 설정값 로드 (실매매 여부)
CONFIG = load_json("config/config.json")
IS_LIVE_MODE = CONFIG.get("is_live_mode", False)

# ✅ pyupbit 업비트 객체 초기화 (실매매에서만 사용)
upbit = pyupbit.Upbit(ACCESS_KEY, SECRET_KEY) if IS_LIVE_MODE else None


def get_balance(currency="KRW"):
    """지정 화폐(KRW, BTC 등) 잔고 조회"""
    if not IS_LIVE_MODE:
        logger.info(f"[SIMULATION] 잔고 조회 - currency: {currency}")
        return 1000000.0  # 시뮬레이션 용 가상 잔고
    try:
        balances = upbit.get_balances()
        for b in balances:
            if b['currency'] == currency:
                return float(b['balance'])
        return 0.0
    except Exception as e:
        logger.error(f"[get_balance] 잔고 조회 실패: {e}")
        if ENABLE_ALERTS:
            send_alert(f"[잔고조회 실패] {currency} → {e}", level="warning")
        return 0.0


def get_current_price(ticker):
    """지정 종목 현재가 조회 (실제 및 모의 동일)"""
    try:
        price = pyupbit.get_current_price(ticker)
        if price is None:
            raise ValueError("현재가 반환값 None")
        return float(price)
    except Exception as e:
        logger.error(f"[get_current_price] 현재가 조회 실패: {e}")
        if ENABLE_ALERTS:
            send_alert(f"[현재가 실패] {ticker} → {e}", level="warning")
        return 0.0


def place_market_buy(ticker, krw_amount):
    """시장가 매수"""
    if not IS_LIVE_MODE:
        logger.warning(f"[SIMULATION] 시장가 매수 생략 - {ticker} {krw_amount} KRW")
        return {"simulated": True, "ticker": ticker, "amount": krw_amount}

    try:
        if krw_amount < 5000:
            raise ValueError("최소 매수 금액은 5000원 이상이어야 합니다.")
        result = upbit.buy_market_order(ticker, krw_amount)
        logger.success(f"[매수완료] {ticker} {krw_amount} KRW → 주문 ID: {result.get('uuid')}")
        return result
    except Exception as e:
        logger.error(f"[place_market_buy] 매수 실패: {e}")
        if ENABLE_ALERTS:
            send_alert(f"[매수 실패] {ticker} → {e}", level="critical")
        return None


def place_market_sell(ticker, volume):
    """시장가 매도"""
    if not IS_LIVE_MODE:
        logger.warning(f"[SIMULATION] 시장가 매도 생략 - {ticker} {volume}개")
        return {"simulated": True, "ticker": ticker, "volume": volume}

    try:
        if volume <= 0:
            raise ValueError("매도 수량이 0 이하입니다.")
        result = upbit.sell_market_order(ticker, volume)
        logger.success(f"[매도완료] {ticker} {volume}개 → 주문 ID: {result.get('uuid')}")
        return result
    except Exception as e:
        logger.error(f"[place_market_sell] 매도 실패: {e}")
        if ENABLE_ALERTS:
            send_alert(f"[매도 실패] {ticker} → {e}", level="critical")
        return None


def get_open_orders(ticker=None):
    """지정 종목의 미체결 주문 조회"""
    if not IS_LIVE_MODE:
        logger.info(f"[SIMULATION] 미체결 주문 없음 (모의)")
        return []
    try:
        orders = upbit.get_order(ticker) if ticker else upbit.get_order()
        return orders
    except Exception as e:
        logger.error(f"[get_open_orders] 주문 조회 실패: {e}")
        return []


def cancel_order(uuid):
    """주문 취소"""
    if not IS_LIVE_MODE:
        logger.info(f"[SIMULATION] 주문 취소 생략 - UUID: {uuid}")
        return {"simulated": True, "uuid": uuid}
    try:
        result = upbit.cancel_order(uuid)
        logger.info(f"[주문취소] UUID: {uuid}")
        return result
    except Exception as e:
        logger.error(f"[cancel_order] 주문 취소 실패: {e}")
        return None

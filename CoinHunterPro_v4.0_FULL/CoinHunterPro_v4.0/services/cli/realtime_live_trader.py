# services/cli/realtime_live_trader.py

import time
import os
import json
import pyupbit
import sys
from datetime import datetime

# ✅ 이 코드로 루트 디렉토리 접근 가능하게 설정
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app_core.infra_control.push_notification import send_telegram_message
from dotenv import load_dotenv

load_dotenv(dotenv_path="./config/.env")  # 환경변수 로드

ACCESS_KEY = os.getenv("UPBIT_ACCESS_KEY")
SECRET_KEY = os.getenv("UPBIT_SECRET_KEY")

upbit = pyupbit.Upbit(ACCESS_KEY, SECRET_KEY)

SYMBOL = "KRW-BTC"
TRADE_AMOUNT_KRW = 6000  # 최대 6000원까지만 매수

def get_current_price():
    return pyupbit.get_current_price(SYMBOL)

def buy_market_order():
    try:
        order = upbit.buy_market_order(SYMBOL, TRADE_AMOUNT_KRW)
        send_telegram_message(f"✅ [실거래 매수] {SYMBOL}\n금액: {TRADE_AMOUNT_KRW:,}₩")
        print("[매수 실행] 주문 성공", order)
    except Exception as e:
        send_telegram_message(f"❌ [실거래 매수 실패] {e}")
        print("[오류] 매수 실패", e)

def main():
    print("[LIVE 거래 시작]")
    while True:
        price = get_current_price()
        print(f"[시세확인] 현재가: {price:,.0f}₩")

        if price and price < 147000000:  # 예시 조건 (147만 원보다 작으면 매수)
            buy_market_order()
            break

        time.sleep(5)

if __name__ == "__main__":
    main()

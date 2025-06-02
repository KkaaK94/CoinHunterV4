# app_core/controller/entry_trigger.py

from utils.logger import log_message
from data_io.json_store.position_manager import save_position
from datetime import datetime

def try_enter_position(ticker, strategy, current_price):
    """
    진입 조건을 판단하여 포지션 진입
    """
    try:
        if strategy.should_enter(ticker, current_price):

            # 전략 자본: 티커별 capital_dict이 우선, 없으면 capital 기본값 사용
            capital = strategy.capital_dict.get(ticker, getattr(strategy, "capital", 10000))
            precision = getattr(strategy, "amount_precision", 6)

            if capital < 1000:  # 최소 진입 기준
                log_message(f"[진입 실패] {ticker}: 자본 부족 (현재 자본: {capital})")
                return False

            amount = round(capital / current_price, precision)
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            position = {
                "ticker": ticker,
                "entry_price": current_price,
                "amount": amount,
                "entry_time": now,
                "status": "HOLD",
                "strategy": strategy.name
            }

            save_position(ticker, position)
            log_message(f"[진입] {ticker} 진입 완료 @ {current_price:,.0f}₩ / 수량: {amount}개 / 전략: {strategy.name}")
            return True

        else:
            log_message(f"[진입 실패] {ticker}: {strategy.name} 조건 미충족")

    except Exception as e:
        log_message(f"[진입 오류] {ticker}: {e}")

    return False

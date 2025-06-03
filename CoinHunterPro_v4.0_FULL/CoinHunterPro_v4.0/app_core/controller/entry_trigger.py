
from datetime import datetime
from utils.logger import log_message, log_position_status
from data_io.json_store.position_manager import save_position

def try_enter_position(ticker, strategy, current_price):
    """
    진입 조건을 판단하여 포지션 진입
    """
    try:
        if strategy.should_enter(ticker, current_price):
            capital = strategy.capital_dict.get(ticker, getattr(strategy, "capital", 10000))
            precision = getattr(strategy, "amount_precision", 6)

            if capital < 1000:
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
            log_position_status(position)  # 실시간 저장
            log_message(f"[진입] {ticker} 진입 완료 @ {current_price:,.0f}₩ / 수량: {amount}개 / 전략: {strategy.name}")
            return True
        else:
            log_message(f"[진입 실패] {ticker}: {strategy.name} 조건 미충족")

    except Exception as e:
        log_message(f"[진입 오류] {ticker}: {e}")

    return False
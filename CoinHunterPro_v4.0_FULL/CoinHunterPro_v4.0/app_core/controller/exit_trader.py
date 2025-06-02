# app_core/controller/exit_trader.py

from utils.logger import log_message
from data_io.json_store.position_manager import load_position, save_position, append_trade_log, update_strategy_performance
from datetime import datetime

def try_exit_position(ticker, strategy, current_price):
    """
    청산 조건을 판단하여 포지션 종료 + 로그/성과 저장
    """
    try:
        position = load_position(ticker)
        if not position:
            return False

        # 외부화된 청산 조건 사용
        if strategy.should_exit(ticker, current_price):
            entry_price = position['entry_price']
            amount = position['amount']
            pnl = (current_price - entry_price) * amount
            pnl_pct = (current_price - entry_price) / entry_price * 100
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            strategy_name = position.get("strategy", strategy.name)

            log_message(
                f"[청산] {ticker} @ {current_price:,.0f}₩ / 수익: {pnl:,.0f}₩ ({pnl_pct:.2f}%) / 전략: {strategy_name}"
            )

            # 💬 개별 거래 로그 저장
            append_trade_log(ticker, {
                "time": now,
                "ticker": ticker,
                "entry_price": entry_price,
                "exit_price": current_price,
                "amount": amount,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "strategy": strategy_name
            })

            # 📊 전략별 누적 성과 저장
            update_strategy_performance(strategy_name, pnl, pnl_pct)

            save_position(ticker, None)
            return True

        else:
            log_message(f"[청산 실패] {ticker}: {strategy.name} 조건 미충족")

    except Exception as e:
        log_message(f"[청산 오류] {ticker}: {e}")

    return False

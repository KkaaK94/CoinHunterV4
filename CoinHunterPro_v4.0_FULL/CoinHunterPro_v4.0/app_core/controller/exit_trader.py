# exit_trader.py

from datetime import datetime
from utils.logger import log_message, log_to_trade_json, log_position_status
from utils.json_manager import load_position, update_exit
from utils.exchange_api import ExchangeAPI

def execute_exit(ticker: str, strategy: object, exchange: ExchangeAPI) -> bool:
    try:
        position = load_position(ticker)
        if not position or position.get("status") != "HOLD":
            log_message(f"[청산스킵] {ticker} 포지션 없음 또는 상태 비활성", level="debug")
            return False

        current_price = exchange.get_current_price(ticker)
        if current_price == 0:
            log_message(f"[가격조회실패] {ticker} 현재 가격을 가져올 수 없음", level="error")
            return False

        if not strategy.should_exit(ticker, current_price):
            log_message(f"[청산실패] {ticker} 전략 조건 미충족", level="debug")
            return False

        amount = position["amount"]
        entry_price = position["entry_price"]
        strategy_name = position.get("strategy", strategy.name)
        mode = position.get("mode", "paper")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        pnl = (current_price - entry_price) * amount
        pnl_pct = ((current_price - entry_price) / entry_price) * 100

        if exchange.is_live:
            order_result = exchange.place_order(ticker, "sell", amount)
            log_to_trade_json(ticker, {
                "event": "exit",
                "time": now,
                "ticker": ticker,
                "entry_price": entry_price,
                "exit_price": current_price,
                "amount": amount,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "strategy": strategy_name,
                "mode": "live",
                "order": order_result
            })
        else:
            log_to_trade_json(ticker, {
                "event": "exit",
                "time": now,
                "ticker": ticker,
                "entry_price": entry_price,
                "exit_price": current_price,
                "amount": amount,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "strategy": strategy_name,
                "mode": "paper"
            })

        update_exit(ticker, current_price, pnl)
        log_position_status({**position, "exit_price": current_price, "status": "CLOSED"})  # 실시간 저장
        log_message(f"[청산완료] {ticker} @ {current_price:,.0f}₩ / 수익: {pnl:,.0f}₩ ({pnl_pct:.2f}%) / 전략: {strategy_name}")
        return True

    except Exception as e:
        log_message(f"[오류] {ticker} 청산 실패: {e}", level="error")
        return False

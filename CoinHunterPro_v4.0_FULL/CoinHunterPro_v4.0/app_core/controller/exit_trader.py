# app_core/controller/exit_trader.py

from utils import exchange_api
from loguru import logger
from utils.json_manager import save_json
from data_io.json_store.position_log import PositionManager
from datetime import datetime
import os

from strategies import rsi, macd, ma_cross

class ExitTrader:
    def __init__(self):
        self.strategies = {
            "RSI": rsi.RSIStrategy(),
            "MACD": macd.MACDStrategy(),
            "MA_CROSS": ma_cross.MACrossStrategy()
        }
        self.position_manager = PositionManager()

    def get_log_path(self, symbol):
        date_str = datetime.now().strftime("%Y%m%d")
        os.makedirs(f"data_io/json_store/exit_logs/{date_str}", exist_ok=True)
        return f"data_io/json_store/exit_logs/{date_str}/{symbol}.json"

    def check(self):
        logger.info("📤 [Exit] 현재 포지션 청산 조건 확인 중...")
        positions = self.position_manager.get_open_positions()

        for pos in positions:
            symbol = pos.get("symbol")
            strategy_name = pos.get("strategy")
            strategy = self.strategies.get(strategy_name)

            if not strategy:
                logger.warning(f"⚠️ 미등록 전략: {strategy_name} → 스킵")
                continue

            try:
                should_exit = strategy.should_exit_position(symbol=symbol)
                if should_exit.get("exit"):
                    logger.success(f"💰 [{strategy_name}] {symbol} 청산 조건 만족")

                    # ✅ 실매도 연동
                    balance = exchange_api.get_balance(symbol.split("-")[1])
                    result = exchange_api.place_market_sell(symbol, balance)

                    self.position_manager.close_position(symbol)
                    save_json(self.get_log_path(symbol), should_exit)
                else:
                    logger.debug(f"🔒 [{strategy_name}] {symbol} 청산 조건 미충족")
            except Exception as e:
                logger.error(f"❌ [{strategy_name}] {symbol} 청산 실패: {e}")

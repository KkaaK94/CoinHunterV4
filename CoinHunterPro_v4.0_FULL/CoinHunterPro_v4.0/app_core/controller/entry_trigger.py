# app_core/controller/entry_trigger.py

from utils import exchange_api
from loguru import logger
from utils.json_manager import save_json
from data_io.json_store.position_log import PositionManager
from datetime import datetime
import os
import pyupbit

from strategies import rsi, macd, ma_cross

class EntrySignalChecker:
    def __init__(self):
        self.primary_strategies = {
            "RSI": rsi.RSIStrategy(),
            "MACD": macd.MACDStrategy(),
            "MA_CROSS": ma_cross.MACrossStrategy()
        }
        self.backup_strategy = macd.MACDStrategy()  # 예시: fallback 전략
        self.position_manager = PositionManager()

    def is_valid_symbol(self, symbol):
        try:
            price = pyupbit.get_current_price(symbol)
            return price is not None
        except:
            return False

    def get_log_path(self, symbol):
        date_str = datetime.now().strftime("%Y%m%d")
        os.makedirs(f"data_io/json_store/entry_logs/{date_str}", exist_ok=True)
        return f"data_io/json_store/entry_logs/{date_str}/{symbol}.json"

    def check(self):
        logger.info("🚀 [Entry] 전략별 진입 시그널 확인 중...")
        for name, strategy in self.primary_strategies.items():
            try:
                signal = strategy.should_enter_position()
                if not signal.get("symbol") or not self.is_valid_symbol(signal.get("symbol")):
                    logger.warning(f"⚠️ [{name}] 심볼 유효성 실패: {signal.get('symbol')}")
                    continue

                if signal.get("enter"):
                    symbol = signal.get("symbol")
                    logger.success(f"✅ [{name}] {symbol} 진입 조건 만족")

                    # ✅ 실매매 연동
                    price = exchange_api.get_current_price(symbol)
                    balance = exchange_api.get_balance("KRW")
                    trade_amount = balance * 0.1  # (예시) 10% 사용

                    result = exchange_api.place_market_buy(symbol, trade_amount)

                    self.position_manager.open_position(symbol, name)
                    save_json(self.get_log_path(symbol), signal)
                else:
                    logger.debug(f"⛔ [{name}] 조건 미충족")
            except Exception as e:
                logger.error(f"❌ [{name}] 진입 시그널 실패: {e}")
                # 백업 전략 fallback 시도
                try:
                    backup_signal = self.backup_strategy.should_enter_position()
                    if backup_signal.get("enter") and self.is_valid_symbol(backup_signal.get("symbol")):
                        symbol = backup_signal.get("symbol")
                        logger.success(f"🔁 백업 전략 진입: {symbol}")
                        self.position_manager.open_position(symbol, "MACD (Fallback)")
                        save_json(self.get_log_path(symbol), backup_signal)
                except Exception as be:
                    logger.error(f"⚠️ 백업 전략도 실패: {be}")

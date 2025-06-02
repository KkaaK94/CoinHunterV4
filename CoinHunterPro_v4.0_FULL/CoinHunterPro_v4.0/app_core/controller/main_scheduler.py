# app_core/controller/main_scheduler.py

import time
from config.strategy_params import build_strategy_instances
from strategies.rsi import RsiStrategy
from app_core.controller.entry_trigger import execute_entry
from app_core.controller.exit_trader import execute_exit
from security.env_config import get_interval, get_env_mode
from utils.exchange_api import ExchangeAPI
from utils.logger import log_message

def run():
    log_message("[시작] CoinHunter 전략 루프 시작")

    strategy_map = {
        "RSI": RsiStrategy,
        # 향후 MACD, MA 등 추가 예정
    }

    strategies = build_strategy_instances(strategy_map)
    exchange = ExchangeAPI(is_live=(get_env_mode() == "production"))

    while True:
        for ticker, strategy in strategies.items():
            try:
                log_message(strategy.log_prefix(ticker) + " 루프 시작", level="debug")

                exited = execute_exit(ticker, strategy, exchange)
                if not exited:
                    execute_entry(ticker, strategy, exchange)

            except Exception as e:
                log_message(f"[오류] {ticker} 처리 중 오류 발생: {e}", level="error")

        time.sleep(get_interval())

if __name__ == "__main__":
    run()

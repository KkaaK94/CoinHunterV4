import time
import traceback
from datetime import datetime
from app_core.controller.entry_trigger import check_entry
from app_core.controller.exit_trader import check_exit
from strategies.rsi import RSIStrategy
from utils.exchange_api import get_current_price
from utils.logger import log_message
from utils.json_manager import load_position, save_position
from config.strategy_params import load_strategy_params
from security.env_config import get_interval
import yaml

# 전략 파라미터 로드 (ticker별 전략 분리 대응 가능)
with open("config/config.yaml", "r") as f:
    config = yaml.safe_load(f)

TICKERS = config["tickers"]
strategy_dict = {}

# 전략 인스턴스 초기화
for ticker in TICKERS:
    strat_name = config["strategies"][ticker]["name"]
    params = config["strategies"][ticker]["params"]
    if strat_name == "RSIStrategy":
        strategy_dict[ticker] = RSIStrategy(params)

while True:
    for ticker in TICKERS:
        try:
            position = load_position(ticker)
            current_price = get_current_price(ticker) or 0
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_message(f"[{now}][{ticker}] 현재가: {current_price:,.0f}원")

            if not position:
                log_message(f"[{now}][상태] {ticker} 무포지션 → 진입 조건 확인")
                if ticker in strategy_dict and check_entry(ticker, current_price, strategy_dict[ticker]):
                    entry_price = current_price
                    position = {
                        "entry_time": now,
                        "entry_price": entry_price,
                        "status": "HOLD"
                    }
                    save_position(ticker, position)
                    log_message(f"[{now}][진입] {ticker} @ {entry_price:,.0f}원")

            elif position and ticker in strategy_dict:
                log_message(f"[{now}][상태] {ticker} 포지션 보유 → 청산 조건 확인")
                if check_exit(ticker, current_price, position, strategy_dict[ticker]):
                    log_message(f"[{now}][청산] {ticker} @ {current_price:,.0f}원")
                    save_position(ticker, None)

        except Exception as e:
            log_message(f"[오류] {ticker}: {e}\n{traceback.format_exc()}")

    time.sleep(get_interval())

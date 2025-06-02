# security/env_config.py

import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv("config/.env")

def get_env():
    return os.getenv("ENV", "development")

def is_production():
    return get_env() == "production"

def get_strategy_mode():
    return os.getenv("STRATEGY_MODE", "paper")

def get_loop_interval():
    return int(os.getenv("LOOP_INTERVAL", 10))

def get_amount_precision():
    return int(os.getenv("AMOUNT_PRECISION", 6))

def get_strategy_capital():
    return float(os.getenv("STRATEGY_CAPITAL", 1000000))

def get_upbit_keys():
    return os.getenv("UPBIT_ACCESS_KEY"), os.getenv("UPBIT_SECRET_KEY")

def alerts_enabled():
    return os.getenv("ENABLE_ALERTS", "false").lower() == "true"

def get_telegram_config():
    return os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")

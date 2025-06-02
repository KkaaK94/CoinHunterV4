# config/strategy_params.py

import yaml
import os
from typing import Dict, Type
from strategies.base_strategy import BaseStrategy

CONFIG_PATH = "config/config.yaml"
DEFAULT_STRATEGY = "RSI"

_cached_config = None

def load_full_config():
    global _cached_config
    if _cached_config is None:
        with open(CONFIG_PATH, "r") as f:
            _cached_config = yaml.safe_load(f)
    return _cached_config

def get_strategy_params(strategy_name: str) -> dict:
    config = load_full_config()
    return config.get("strategy", {}).get(strategy_name, {})

def get_assigned_strategy(ticker: str) -> str:
    config = load_full_config()
    return config.get("assignments", {}).get(ticker, DEFAULT_STRATEGY)

def get_capital_allocation(ticker: str) -> float:
    config = load_full_config()
    return config.get("capital", {}).get(ticker, 0)

def get_precision(ticker: str) -> int:
    config = load_full_config()
    return config.get("precision", {}).get(ticker, 6)

def build_strategy_instances(strategy_class_map: Dict[str, Type[BaseStrategy]]) -> Dict[str, BaseStrategy]:
    config = load_full_config()
    instances = {}

    for ticker, strategy_name in config.get("assignments", {}).items():
        strategy_class = strategy_class_map.get(strategy_name)
        if not strategy_class:
            print(f"[경고] '{strategy_name}' 클래스가 strategy_class_map에 없습니다. → 티커 {ticker}는 생략됨")
            continue

        try:
            params = get_strategy_params(strategy_name)
            capital = get_capital_allocation(ticker)
            precision = get_precision(ticker)

            instance = strategy_class(params=params, capital=capital, precision=precision)
            instances[ticker] = instance
        except Exception as e:
            print(f"[오류] '{ticker}' 전략 인스턴스 생성 실패: {e}")

    return instances

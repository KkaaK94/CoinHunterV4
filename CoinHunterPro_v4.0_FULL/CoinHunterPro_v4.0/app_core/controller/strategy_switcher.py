# app_core/controller/strategy_switcher.py

from datetime import datetime, timedelta
from utils.logger import log_message
from utils.json_manager import load_strategy_scores
from config.strategy_params import build_strategy_instances

last_switch_time = {}

def compute_score(metrics):
    return (
        metrics.get("sharpe", 0) * 0.5 +
        metrics.get("win_rate", 0) * 0.3 -
        metrics.get("drawdown", 0) * 0.2
    )

def switch_strategy_if_needed(ticker, current_strategy, strategy_instances: dict) -> str:
    global last_switch_time
    scores = load_strategy_scores()

    now = datetime.now()
    last_switched = last_switch_time.get(ticker, now - timedelta(days=1))
    if (now - last_switched) < timedelta(hours=24):
        log_message(f"[전략유지] {ticker}: 최근 변경 이력 존재 → 스위칭 제한")
        return current_strategy

    best_strategy = current_strategy
    best_score = -float("inf")

    for strategy_name, metrics in scores.get(ticker, {}).items():
        score = compute_score(metrics)
        if score > best_score:
            best_score = score
            best_strategy = strategy_name

    if best_strategy != current_strategy:
        last_switch_time[ticker] = now
        log_message(f"[전략변경] {ticker}: {current_strategy} → {best_strategy} (score: {best_score:.2f})")
        return best_strategy
    else:
        log_message(f"[전략유지] {ticker}: {current_strategy} 유지 (score: {best_score:.2f})")
        return current_strategy

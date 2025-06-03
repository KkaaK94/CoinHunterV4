import json
import subprocess
import hashlib
import time
import sys
import os
from pathlib import Path
from datetime import datetime

# 상위 디렉토리 접근용
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from interface.reports.performance_report import generate_performance_report

STATUS_FILE = "data_io/json_store/allocator_status.json"
SCORES_FILE = "data_io/json_store/strategy_scores.json"
WEIGHTS_FILE = "data_io/json_store/capital_weights.json"
SCORE_HISTORY_FILE = "data_io/json_store/strategy_score_history.json"
POSITION_LOG_FILE = "data_io/logs/position_log.json"

def get_score_hash(score_dict):
    return hashlib.md5(json.dumps(score_dict, sort_keys=True).encode()).hexdigest()

def has_recently_executed(min_interval_sec=600):
    if not Path(STATUS_FILE).exists():
        return False
    with open(STATUS_FILE, "r") as f:
        status = json.load(f)
    last_time = status.get("last_run_time", 0)
    return time.time() - last_time < min_interval_sec

def should_run(current_scores):
    if has_recently_executed():
        return False
    if not Path(STATUS_FILE).exists():
        return True
    with open(STATUS_FILE, "r") as f:
        status = json.load(f)
    prev_hash = status.get("last_score_hash")
    new_hash = get_score_hash(current_scores)
    return prev_hash != new_hash

def update_status(current_scores):
    status = {
        "last_run_time": time.time(),
        "last_score_hash": get_score_hash(current_scores)
    }
    with open(STATUS_FILE, "w") as f:
        json.dump(status, f, indent=2)

def save_strategy_score_history(current_scores):
    history = []
    if Path(SCORE_HISTORY_FILE).exists():
        try:
            with open(SCORE_HISTORY_FILE, "r") as f:
                history = json.load(f)
        except json.JSONDecodeError:
            history = []
    history.append({
        "timestamp": datetime.now().isoformat(),
        "scores": current_scores
    })
    with open(SCORE_HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def log_position_status(position_data):
    with open(POSITION_LOG_FILE, "w") as f:
        json.dump(position_data, f, indent=2)

def main():
    if not Path(SCORES_FILE).exists():
        print(f"[오류] {SCORES_FILE} 파일이 존재하지 않습니다.")
        return

    with open(SCORES_FILE, "r") as f:
        scores = json.load(f)

    if not should_run(scores):
        print("[SKIP] 최근 실행되었거나 점수 변경 없음")
        return

    print("[실행] 자본 재배분 및 리포트 생성 시작")

    subprocess.run([
        "python", "services/cli/capital_allocator_cli.py",
        "--capital", "10000000",
        "--threshold", "0.05",
        "--log"
    ])

    with open(WEIGHTS_FILE, "r") as f:
        weights = json.load(f)

    metrics = {}
    for strat in scores:
        metrics[strat] = {
            "total_return": round(scores[strat], 4),
            "mdd": round(0.1 + 0.05 * (1 - scores[strat]), 2),
            "sharpe": round(1.0 + scores[strat], 2),
            "win_trades": 12,
            "trade_count": 20,
            "avg_holding_sec": 4000
        }

    generate_performance_report(metrics)
    save_strategy_score_history(scores)

    position_data = {
        "strategy": max(scores, key=scores.get),
        "position": "LONG",
        "entry_price": 100.0,
        "current_price": 105.0,
        "profit": 5.0
    }
    log_position_status(position_data)

    update_status(scores)
    print("[완료] 자본 재배분 및 리포트 생성 완료")

if __name__ == "__main__":
    main()

# services/cli/capital_allocator_cli.py

import argparse
import json
import csv
import random
import hashlib
import time
from pathlib import Path
from app_core.analytics.capital_allocator import (
    load_strategy_scores,
    allocate_capital,
    allocate_by_group,
    save_capital_weights_enhanced
)

STATUS_FILE = "data_io/json_store/allocator_status.json"

def has_recently_executed(min_interval_sec=600):
    if not Path(STATUS_FILE).exists():
        return False
    try:
        status = json.load(open(STATUS_FILE))
        last_time = status.get("last_run_time", 0)
        return time.time() - last_time < min_interval_sec
    except Exception:
        return False

def get_score_hash(score_dict):
    return hashlib.md5(json.dumps(score_dict, sort_keys=True).encode()).hexdigest()

def should_run(current_scores):
    if has_recently_executed():
        return False
    try:
        status = json.load(open(STATUS_FILE)) if Path(STATUS_FILE).exists() else {}
        prev_hash = status.get("last_score_hash")
        new_hash = get_score_hash(current_scores)
        return prev_hash != new_hash
    except Exception:
        return True

def update_status(current_scores):
    status = {
        "last_run_time": time.time(),
        "last_score_hash": get_score_hash(current_scores)
    }
    json.dump(status, open(STATUS_FILE, "w"), indent=2)

def simulate_scores(strategies: list[str]) -> dict:
    return {s: round(random.uniform(0.01, 1.0), 4) for s in strategies}

def save_weights_csv(weights: dict, csv_path: str):
    with open(csv_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["strategy", "allocated_capital"])
        for strat, capital in weights.items():
            writer.writerow([strat, capital])
    print(f"[CSV 저장완료] → {csv_path}")

def main():
    parser = argparse.ArgumentParser(description="전략 점수 기반 자본 배분 CLI")
    parser.add_argument("--capital", type=float, default=1_000_000, help="총 운용 자본")
    parser.add_argument("--threshold", type=float, default=0.05, help="전략 최소 점수 임계치")
    parser.add_argument("--grouping", action="store_true", help="전략 그룹별 분배 여부")
    parser.add_argument("--group_file", type=str, default="config/strategy_groups.json", help="전략 그룹 매핑 파일 경로")
    parser.add_argument("--log", action="store_true", help="배분 결과를 log.json 저장")
    parser.add_argument("--csv", type=str, help="CSV 저장 경로 (예: output/weights.csv)")
    parser.add_argument("--simulate", action="store_true", help="무작위 전략 점수 시뮬레이션")
    args = parser.parse_args()

    if args.simulate:
        strategies = ["RSI", "MACD", "BOLL", "EMA"]
        scores = simulate_scores(strategies)
        print(f"[시뮬레이션 점수 생성] {scores}")
    else:
        scores = load_strategy_scores()

    if not should_run(scores):
        print("[SKIP] 최근 실행되었거나 점수 변경 없음")
        return

    if args.grouping:
        try:
            with open(args.group_file, "r") as f:
                group_map = json.load(f)
        except Exception as e:
            print(f"[그룹로드 실패] {e}")
            return

        weights = allocate_by_group(scores, group_map, args.capital)
        method = "group_weighted"
    else:
        weights = allocate_capital(scores, total_capital=args.capital, weight_threshold=args.threshold)
        method = f"threshold_{args.threshold}"

    save_capital_weights_enhanced(
        weights=weights,
        scores=scores,
        total_capital=args.capital,
        method=method
    )

    if args.csv:
        save_weights_csv(weights, args.csv)

    if args.log:
        with open("data_io/json_store/capital_weights_log.json", "w") as f:
            json.dump(weights, f, indent=2, ensure_ascii=False)
        print("[로그 저장완료] → capital_weights_log.json")

    update_status(scores)

if __name__ == "__main__":
    main()

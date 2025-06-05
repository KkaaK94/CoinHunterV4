# infra_control/capital_allocator.py

import os
from utils.json_manager import load_json, save_json
from utils.logger import logger
from config import config

STRATEGY_SCORE_PATH = config.get("score_file_path", "data_io/json_store/strategy_scores.json")
WEIGHT_OUTPUT_PATH = config.get("weight_file_path", "data_io/json_store/capital_weights.json")

MIN_ROI = config.get("capital_min_roi", 0.5)
MIN_COUNT = config.get("min_trade_count", 5)
TOP_N = config.get("capital_top_n", 5)

def allocate_capital_weights():
    scores = load_json(STRATEGY_SCORE_PATH, default=[])

    filtered = [
        s for s in scores
        if s.get("roi", 0) >= MIN_ROI and s.get("total_count", 0) >= MIN_COUNT
    ]

    filtered = sorted(filtered, key=lambda x: x["roi"], reverse=True)[:TOP_N]

    if not filtered:
        logger.warning("[Capital] 조건에 부합하는 전략 없음 → 비중 파일 생성 안됨")
        return

    total_roi = sum([s["roi"] for s in filtered])
    weights = {}

    for s in filtered:
        name = s["strategy_name"]
        roi = s["roi"]
        weight = round(roi / total_roi, 4)
        weights[name] = weight

    save_json(WEIGHT_OUTPUT_PATH, weights)
    logger.success(f"[Capital] 전략 자본 비중 저장 완료: {WEIGHT_OUTPUT_PATH} → {weights}")

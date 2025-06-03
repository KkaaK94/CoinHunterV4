# app_core/analytics/capital_allocator.py

import json
import os
from typing import Dict
from datetime import datetime


def allocate_capital(
    scores: Dict[str, float],
    total_capital: float,
    weight_threshold: float = 0.05
) -> Dict[str, float]:
    """
    전략 점수를 기반으로 자본 배분 계산. 특정 점수 이하 전략은 제외 가능.

    Args:
        scores (Dict): 전략별 점수
        total_capital (float): 총 운용 자본
        weight_threshold (float): 전략 최소 점수 기준

    Returns:
        Dict: 전략별 자본 배분
    """
    filtered_scores = {k: v for k, v in scores.items() if v >= weight_threshold}
    if not filtered_scores:
        print(f"[자본배분] 모든 전략이 임계치({weight_threshold}) 미만 → 균등 분배")
        filtered_scores = {k: 1.0 for k in scores}

    total_score = sum(filtered_scores.values())

    if total_score == 0:
        equal_share = total_capital / len(filtered_scores)
        return {k: round(equal_share, 2) for k in filtered_scores}

    allocation = {
        k: round((v / total_score) * total_capital, 2)
        for k, v in filtered_scores.items()
    }

    print(f"[자본배분] 자본 배분 결과: {allocation}")
    return allocation


def select_top_n_scores(scores: Dict[str, float], n: int) -> Dict[str, float]:
    sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    selected = dict(sorted_items[:n])
    print(f"[전략선택] 상위 {n}개 전략 선택: {selected}")
    return selected


def allocate_by_group(
    scores: Dict[str, float],
    groups: Dict[str, str],
    total_capital: float,
    group_weights: Dict[str, float] = None
) -> Dict[str, float]:
    """
    전략 그룹별 비중 기반 배분 → 그룹 내부는 점수 기준 분배

    Args:
        scores: 전체 전략 점수
        groups: {"RSI": "모멘텀", "PER": "가치"}
        total_capital: 전체 자본
        group_weights: {"모멘텀": 0.6, "가치": 0.4}

    Returns:
        전체 전략별 자본 배분 dict
    """
    if group_weights is None:
        unique_groups = set(groups.values())
        group_weights = {g: 1.0 / len(unique_groups) for g in unique_groups}

    capital_alloc = {}

    for group, group_weight in group_weights.items():
        group_strategies = {k: v for k, v in scores.items() if groups.get(k) == group}
        group_cap = total_capital * group_weight
        print(f"[그룹배분] {group} 그룹에 {group_cap}원 배분")
        partial_alloc = allocate_capital(group_strategies, group_cap)
        capital_alloc.update(partial_alloc)

    return capital_alloc


def save_capital_weights_enhanced(
    weights: Dict[str, float],
    scores: Dict[str, float],
    total_capital: float,
    method: str,
    path: str = "data_io/json_store/capital_weights.json"
):
    data = {
        "timestamp": datetime.now().isoformat(),
        "total_capital": total_capital,
        "allocation_method": method,
        "strategies": [
            {
                "name": strat,
                "score": round(scores.get(strat, 0), 4),
                "weight": round(weights[strat] / total_capital, 4),
                "capital_allocated": round(weights[strat], 2)
            }
            for strat in weights
        ]
    }

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"[저장완료] 자본 배분 결과 저장됨 → {path}")


def load_strategy_scores(path: str = "data_io/json_store/strategy_scores.json") -> Dict[str, float]:
    if not os.path.exists(path):
        print(f"[로드실패] 점수 파일 없음 → {path}")
        return {}

    with open(path, "r") as f:
        try:
            scores = json.load(f)
            print(f"[로드완료] 전략 점수 불러옴: {scores}")
            return scores
        except json.JSONDecodeError:
            print(f"[로드실패] JSON 파싱 오류 → {path}")
            return {}

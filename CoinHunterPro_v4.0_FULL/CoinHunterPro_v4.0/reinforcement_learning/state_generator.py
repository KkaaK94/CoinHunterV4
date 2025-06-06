import os
import sys
import pandas as pd
from datetime import datetime

# 상위 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.json_manager import load_json

# 경로 설정
SCORE_PATH = "data_io/json_store/strategy_scores.json"
WEIGHT_PATH = "data_io/json_store/capital_weights.json"
POLICY_PATH = "reinforcement_learning/policy_meta.json"

def generate_state():
    scores = load_json(SCORE_PATH, [])
    weights = load_json(WEIGHT_PATH, {})
    policy = load_json(POLICY_PATH, {})

    # 파일 비정상 구조 방지
    if not isinstance(scores, list) or len(scores) == 0:
        print("❌ strategy_scores.json: 유효한 리스트 구조 아님")
        return {}

    df = pd.DataFrame(scores)

    # weight 매핑 및 타입 안정화
    df["weight"] = df["strategy_name"].map(weights).fillna(0)
    df["weight"] = df["weight"].astype(float)

    # 상태 딕셔너리 구성
    state = {
        "total_strategies": len(df),
        "avg_roi": df["roi"].mean(),
        "avg_win_rate": df["win_rate"].mean(),
        "total_weight": sum(float(v) for v in weights.values()),
        "current_policy": policy.get("current_policy", "none"),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    return state

# 디버깅용 단독 실행
if __name__ == "__main__":
    s = generate_state()
    print("🔍 상태:", s)

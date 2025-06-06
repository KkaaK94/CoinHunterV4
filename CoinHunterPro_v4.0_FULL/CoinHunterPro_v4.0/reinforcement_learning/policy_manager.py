# reinforcement_learning/policy_manager.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import os
import json
from datetime import datetime
from state_generator import generate_state
from utils.json_manager import load_json, save_json




POLICY_META_PATH = "reinforcement_learning/policy_meta.json"


def apply_new_policy(policy_name: str, description: str = ""):
    """새로운 정책을 적용하고 policy_meta.json에 기록"""
    meta = load_json(POLICY_META_PATH, default={})
    history = meta.get("history", [])

    # 기존 정책 로그 기록
    if meta.get("current_policy"):
        history.append({
            "policy": meta["current_policy"],
            "applied_at": meta.get("applied_at", datetime.now().isoformat()),
            "description": meta.get("description", "이전 정책")
        })

    # 현재 정책 갱신
    meta["current_policy"] = policy_name
    meta["applied_at"] = datetime.now().isoformat()
    meta["description"] = description
    meta["history"] = history

    save_json(POLICY_META_PATH, meta)
    print(f"[Policy] ✅ 정책 적용 완료: {policy_name}")


def recommend_policy():
    """현재 상태 기반으로 정책 추천 (샘플 룰 기반)"""
    state = generate_state()
    if not state:
        print("[Policy] 상태 생성 실패. 정책 추천 불가.")
        return None

    top_strategy = state["top_strategy"]
    roi = state["top_roi"]

    if roi > 1.5:
        return {
            "recommend": f"{top_strategy}_v1",
            "reason": f"Top ROI {roi:.2f}% → 강력 추천"
        }
    else:
        return {
            "recommend": None,
            "reason": f"ROI {roi:.2f}%로 추천 정책 없음"
        }


if __name__ == "__main__":
    rec = recommend_policy()
    if rec and rec["recommend"]:
        apply_new_policy(rec["recommend"], rec["reason"])
    else:
        print("[Policy] 정책 변경 없음.")

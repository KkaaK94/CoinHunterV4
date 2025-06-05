import os
import json
from datetime import datetime
from utils.json_manager import load_json, save_json

POLICY_META_PATH = "reinforcement_learning/policy_meta.json"

def apply_new_policy(policy_name: str, description: str = ""):
    """새로운 정책을 적용하고 policy_meta.json에 기록"""
    meta = load_json(POLICY_META_PATH, default={})
    history = meta.get("history", [])

    # 이전 정책 로그로 history에 누적
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
    print(f"[Policy] 정책 적용 완료: {policy_name}")

import os
import json
from datetime import datetime
from pathlib import Path
from pymongo import MongoClient

# JSON 로그 저장: 티커별/날짜별 파일 분리
def log_to_trade_json(ticker, log):
    date_str = datetime.now().strftime("%Y%m%d")
    dir_path = os.path.join("data_io/json_store/trade_log", ticker)
    Path(dir_path).mkdir(parents=True, exist_ok=True)

    file_path = os.path.join(dir_path, f"{date_str}.json")
    logs = []

    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                logs = json.load(f)
        except json.JSONDecodeError:
            logs = []

    logs.append(log)
    logs = logs[-100:]  # 최근 100건 유지

    with open(file_path, 'w') as f:
        json.dump(logs, f, indent=2, ensure_ascii=False, default=str)

# MongoDB 저장 (선택적 활성화)
def log_to_trade_db(log, db_name="coinhunter", collection="trades"):
    try:
        mongo_url = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        client = MongoClient(mongo_url)
        db = client[db_name]
        db[collection].insert_one(log)
    except Exception as e:
        print(f"[DB 로그 실패] {e}")

def log_message(message, extra=None):
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{time_str}] {message}")
    if extra:
        print(f" └▶ {extra}")
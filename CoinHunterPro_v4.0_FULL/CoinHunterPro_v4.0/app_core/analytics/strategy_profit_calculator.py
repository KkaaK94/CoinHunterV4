# app_core/analytics/strategy_profit_calculator.py

import os
import json
from datetime import datetime
from utils.json_manager import load_json
from config import config

def calculate_strategy_profits(log_dir=None):
    if not log_dir:
        log_dir = config.get("strategy_log_dir", "data_io/json_store/trade_log")

    roi_filter = config.get("roi_filter", 0.0)
    strategy_name_filter = config.get("strategy_name_filter", [])

    scores = []
    if not os.path.exists(log_dir):
        return scores

    for date_folder in sorted(os.listdir(log_dir)):
        folder_path = os.path.join(log_dir, date_folder)
        if not os.path.isdir(folder_path):
            continue

        for filename in os.listdir(folder_path):
            filepath = os.path.join(folder_path, filename)
            with open(filepath, "r") as f:
                trades = json.load(f)

            strategy_data = {}
            for trade in trades:
                name = trade.get("strategy_name")
                roi = trade.get("roi", 0)
                profit = trade.get("profit", 0)
                win = trade.get("win", False)

                if not name or (strategy_name_filter and name not in strategy_name_filter):
                    continue

                if name not in strategy_data:
                    strategy_data[name] = {
                        "total_roi": 0,
                        "total_profit": 0,
                        "win_count": 0,
                        "total_count": 0
                    }

                s = strategy_data[name]
                s["total_roi"] += roi
                s["total_profit"] += profit
                s["win_count"] += 1 if win else 0
                s["total_count"] += 1

            for name, data in strategy_data.items():
                if data["total_count"] == 0:
                    continue
                avg_roi = data["total_roi"] / data["total_count"]
                win_rate = (data["win_count"] / data["total_count"]) * 100

                if avg_roi < roi_filter:
                    continue

                scores.append({
                    "strategy_name": name,
                    "roi": round(avg_roi, 2),
                    "profit": round(data["total_profit"], 2),
                    "win_rate": round(win_rate, 2),
                    "total_count": data["total_count"]
                })

    return sorted(scores, key=lambda x: x["roi"], reverse=True)

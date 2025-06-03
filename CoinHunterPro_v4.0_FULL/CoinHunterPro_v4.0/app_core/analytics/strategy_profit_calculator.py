# app_core/analytics/strategy_profit_calculator.py

import pandas as pd
import numpy as np
from datetime import datetime


def calculate_profit(trade_logs: list[dict]) -> dict:
    trades = []
    entry = None

    for log in trade_logs:
        if log.get("event") == "entry_signal":
            entry = {
                "entry_price": log.get("entry_price"),
                "entry_time": log.get("timestamp") or log.get("time") or datetime.now().isoformat()
            }
        elif log.get("event") == "exit_signal" and entry:
            exit_price = log.get("exit_price")
            exit_time = log.get("timestamp") or log.get("time") or datetime.now().isoformat()

            pnl = (exit_price - entry["entry_price"]) / entry["entry_price"]
            duration = (pd.to_datetime(exit_time) - pd.to_datetime(entry["entry_time"])).total_seconds()

            trades.append({
                "entry_price": entry["entry_price"],
                "exit_price": exit_price,
                "pnl": pnl,
                "duration_sec": duration
            })

            entry = None  # reset after one trade

    df = pd.DataFrame(trades)

    if df.empty:
        return {
            "total_return": 0.0,
            "mdd": 0.0,
            "sharpe": 0.0,
            "avg_holding_sec": 0.0,
            "trade_count": 0
        }

    df["cumulative_return"] = (1 + df["pnl"]).cumprod()
    peak = df["cumulative_return"].cummax()
    drawdown = (df["cumulative_return"] - peak) / peak
    mdd = drawdown.min()

    sharpe = df["pnl"].mean() / df["pnl"].std() * np.sqrt(252) if df["pnl"].std() != 0 else 0

    return {
        "total_return": round(df["cumulative_return"].iloc[-1] - 1, 4),
        "mdd": round(mdd, 4),
        "sharpe": round(sharpe, 4),
        "avg_holding_sec": round(df["duration_sec"].mean(), 2),
        "trade_count": len(df)
    }

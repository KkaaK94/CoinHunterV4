# app_core/analytics/strategy_profit_calculator.py

import os
import pandas as pd
import numpy as np
from datetime import datetime
import json

from interface.reports.performance_report import generate_performance_report

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

            entry = None  # reset

    df = pd.DataFrame(trades)

    if df.empty:
        return {
            "total_return": 0.0,
            "mdd": 0.0,
            "sharpe": 0.0,
            "avg_holding_sec": 0.0,
            "trade_count": 0,
            "win_trades": 0
        }

    df["cumulative_return"] = (1 + df["pnl"]).cumprod()
    peak = df["cumulative_return"].cummax()
    drawdown = (df["cumulative_return"] - peak) / peak
    mdd = drawdown.min()

    sharpe = df["pnl"].mean() / df["pnl"].std() * np.sqrt(252) if df["pnl"].std() != 0 else 0
    win_trades = (df["pnl"] > 0).sum()

    return {
        "total_return": round(df["cumulative_return"].iloc[-1] - 1, 4),
        "mdd": round(mdd, 4),
        "sharpe": round(sharpe, 4),
        "avg_holding_sec": round(df["duration_sec"].mean(), 2),
        "trade_count": len(df),
        "win_trades": int(win_trades)
    }


def calculate_strategy_profits(strategy_log_dir: str = "data_io/json_store/strategy_logs") -> dict:
    """
    전략별 JSON 로그 디렉토리를 스캔하여 성과를 계산합니다.
    """
    metrics = {}

    for filename in os.listdir(strategy_log_dir):
        if filename.endswith(".json"):
            strategy_name = filename.replace(".json", "")
            filepath = os.path.join(strategy_log_dir, filename)
            try:
                with open(filepath, "r") as f:
                    logs = json.load(f)
                metrics[strategy_name] = calculate_profit(logs)
            except Exception as e:
                print(f"[오류] {strategy_name} 처리 중 실패: {e}")

    return metrics


def finalize_profit_report():
    """
    전략 수익률 계산 후 HTML + PDF 리포트 자동 저장
    """
    metrics = calculate_strategy_profits()
    generate_performance_report(
        metrics,
        output_path="interface/reports/strategy_report.html",
        pdf_output_path="interface/reports/strategy_report.pdf"
    )


if __name__ == "__main__":
    finalize_profit_report()

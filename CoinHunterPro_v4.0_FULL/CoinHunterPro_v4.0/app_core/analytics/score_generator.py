import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.backends.backend_pdf
import smtplib
from email.message import EmailMessage
from datetime import datetime

# 경로 설정
TRADE_LOG_PATH = "data_io/json_store/trade_log"
SCORES_PATH = "data_io/json_store/strategy_scores.json"
SCORES_DETAIL_PATH = "data_io/json_store/strategy_scores_detail.json"
CAPITAL_WEIGHTS_PATH = "data_io/json_store/capital_weights.json"
SCORE_HISTORY_PATH = "data_io/json_store/score_history.json"
REPORT_PDF_PATH = "reports/strategy_report.pdf"

# 설정값
MIN_TRADES = 5
TOP_N = 3

# 이메일 설정
EMAIL_SENDER = "your_email@example.com"
EMAIL_RECEIVER = "recipient@example.com"
SMTP_SERVER = "smtp.example.com"
SMTP_PORT = 587
EMAIL_USERNAME = "your_email@example.com"
EMAIL_PASSWORD = "your_email_password"

_cached_scores = None

def load_trade_logs():
    all_logs = {}
    for ticker in os.listdir(TRADE_LOG_PATH):
        ticker_path = os.path.join(TRADE_LOG_PATH, ticker)
        if not os.path.isdir(ticker_path):
            continue
        all_logs[ticker] = {}
        for fname in os.listdir(ticker_path):
            if not fname.endswith(".json") or not fname.startswith("trade_"):
                continue
            fpath = os.path.join(ticker_path, fname)
            with open(fpath, "r") as f:
                try:
                    logs = json.load(f)
                    for log in logs:
                        strat = log.get("strategy", "unknown")
                        if strat not in all_logs[ticker]:
                            all_logs[ticker][strat] = []
                        all_logs[ticker][strat].append(log)
                except:
                    print(f"⚠️ 오류: {fpath} 파일 로드 실패")
    return all_logs

def calculate_metrics(logs):
    if len(logs) == 0:
        return None

    df = pd.DataFrame(logs)
    df = df[df["event"] == "exit"]
    if df.empty:
        return None

    df["pnl"] = df["pnl"].astype(float)
    df["entry_time"] = pd.to_datetime(df["time"])
    df.sort_values("entry_time", inplace=True)

    total_pnl = df["pnl"].sum()
    avg_pnl = df["pnl"].mean()
    median_pnl = df["pnl"].median()
    win_rate = (df["pnl"] > 0).mean()
    sharpe = df["pnl"].mean() / (df["pnl"].std() + 1e-9)
    max_dd = (df["pnl"].cumsum().cummax() - df["pnl"].cumsum()).max()
    duration_days = (df["entry_time"].max() - df["entry_time"].min()).days + 1
    cagr = (1 + df["pnl"].sum()) ** (365 / duration_days) - 1
    calmar = cagr / (max_dd + 1e-9)

    return {
        "num_trades": len(df),
        "total_pnl": total_pnl,
        "avg_pnl": avg_pnl,
        "median_pnl": median_pnl,
        "win_rate": win_rate,
        "sharpe": sharpe,
        "max_drawdown": max_dd,
        "cagr": cagr,
        "calmar_ratio": calmar
    }

def compute_score(metrics):
    return (
        metrics.get("sharpe", 0) * 0.4 +
        metrics.get("win_rate", 0) * 0.3 +
        metrics.get("cagr", 0) * 0.2 -
        metrics.get("max_drawdown", 0) * 0.1
    )

def generate_scores():
    global _cached_scores
    if _cached_scores is not None:
        return _cached_scores

    all_logs = load_trade_logs()
    scores = {}
    score_details = {}
    capital_weights = {}

    for ticker, strategies in all_logs.items():
        scores[ticker] = {}
        score_details[ticker] = {}
        for strategy, logs in strategies.items():
            if len(logs) < MIN_TRADES:
                continue
            metrics = calculate_metrics(logs)
            if not metrics:
                continue
            score = compute_score(metrics)
            scores[ticker][strategy] = round(score, 4)
            score_details[ticker][strategy] = {
                "score": score,
                "metrics": metrics
            }

        top_strategies = sorted(scores[ticker].items(), key=lambda x: x[1], reverse=True)[:TOP_N]
        capital_weights[ticker] = {s: v for s, v in top_strategies}

    with open(SCORES_PATH, "w") as f:
        json.dump(scores, f, indent=2, ensure_ascii=False)

    with open(SCORES_DETAIL_PATH, "w") as f:
        json.dump(score_details, f, indent=2, ensure_ascii=False)

    with open(CAPITAL_WEIGHTS_PATH, "w") as f:
        json.dump(capital_weights, f, indent=2, ensure_ascii=False)

    # 전략 성능 변화 추적
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if os.path.exists(SCORE_HISTORY_PATH):
        with open(SCORE_HISTORY_PATH, "r") as f:
            history = json.load(f)
    else:
        history = {}
    history[timestamp] = scores
    with open(SCORE_HISTORY_PATH, "w") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

    _cached_scores = scores
    return scores

def plot_strategy_performance(score_details, output_path=REPORT_PDF_PATH):
    pdf = matplotlib.backends.backend_pdf.PdfPages(output_path)
    for ticker, strategies in score_details.items():
        for strategy, detail in strategies.items():
            metrics = detail["metrics"]
            fig, ax = plt.subplots(figsize=(6, 4))
            sns.barplot(x=list(metrics.keys()), y=list(metrics.values()), ax=ax)
            ax.set_title(f"{ticker} - {strategy} Metrics")
            pdf.savefig(fig)
            plt.close()
    pdf.close()
    print(f"[리포트] PDF 성과 리포트 저장 완료: {output_path}")

def send_email_with_report(report_path):
    msg = EmailMessage()
    msg["Subject"] = "전략 성과 리포트"
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg.set_content("첨부된 전략 성과 리포트를 확인해주세요.")

    with open(report_path, "rb") as f:
        file_data = f.read()
        file_name = os.path.basename(report_path)
    msg.add_attachment(file_data, maintype="application", subtype="pdf", filename=file_name)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        server.send_message(msg)
    print(f"[이메일] 리포트 이메일 전송 완료: {EMAIL_RECEIVER}")

if __name__ == "__main__":
    scores = generate_scores()
    with open(SCORES_DETAIL_PATH, "r") as f:
        details = json.load(f)
    plot_strategy_performance(details)
    send_email_with_report(REPORT_PDF_PATH)

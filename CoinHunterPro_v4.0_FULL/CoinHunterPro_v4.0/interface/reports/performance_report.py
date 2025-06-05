# interface/reports/performance_report.py

import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from loguru import logger
from utils.json_manager import save_json
from config.config_loader import get_config

CONFIG = get_config()
STRATEGY_NAME_FILTER = CONFIG.get("strategy_name_filter", [])
STRATEGY_ROI_FILTER = CONFIG.get("strategy_roi_filter", 0.0)
TOP_N = CONFIG.get("report_top_n", 5)
REPORT_META_FILE = CONFIG.get("report_meta_file", "interface/reports/report_meta.json")

def filter_strategies(data):
    filtered = []
    for strategy in data:
        name = strategy.get("strategy_name", "")
        roi = strategy.get("roi", 0)
        if roi >= STRATEGY_ROI_FILTER and (not STRATEGY_NAME_FILTER or name in STRATEGY_NAME_FILTER):
            filtered.append(strategy)
    return filtered

def generate_performance_report(metrics: list, output_path="report.html", pdf_output_path=None):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    filtered = filter_strategies(metrics)
    sorted_data = sorted(filtered, key=lambda x: x.get("roi", 0), reverse=True)

    logger.info(f"[REPORT] 필터링 후 전략 수: {len(sorted_data)}")
    top_strategies = sorted_data[:TOP_N]

    # HTML 텍스트 생성
    html_content = f"""
    <html>
        <head>
            <meta charset="UTF-8">
            <title>CoinHunterPro 전략 성과 리포트</title>
            <style>
                body {{ font-family: 'Arial'; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: center; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h2>📈 CoinHunterPro 전략 성과 리포트</h2>
            <p>📅 생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <table>
                <tr>
                    <th>전략 이름</th>
                    <th>ROI (%)</th>
                    <th>총 거래 수</th>
                    <th>승률 (%)</th>
                    <th>누적 손익</th>
                </tr>
    """

    for s in top_strategies:
        html_content += f"""
        <tr>
            <td>{s.get("strategy_name")}</td>
            <td>{s.get("roi", 0):.2f}</td>
            <td>{s.get("total_count", 0)}</td>
            <td>{s.get("win_rate", 0):.2f}</td>
            <td>{s.get("profit", 0):,.0f}</td>
        </tr>
        """

    html_content += """
            </table>
        </body>
    </html>
    """

    # 저장
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    logger.success(f"[REPORT] HTML 리포트 저장 완료: {output_path}")

    # 메타정보 저장
    save_json(REPORT_META_FILE, {
        "generated_at": datetime.now().isoformat(),
        "top_strategies": top_strategies
    })

    # (선택) PDF 저장 기능
    if pdf_output_path:
        try:
            import pdfkit
            pdfkit.from_file(output_path, pdf_output_path)
            logger.success(f"[REPORT] PDF 저장 완료: {pdf_output_path}")
        except Exception as e:
            logger.warning(f"[REPORT] PDF 변환 실패: {e}")

def plot_top_strategies(metrics, output_dir="interface/reports/"):
    os.makedirs(output_dir, exist_ok=True)
    df = pd.DataFrame(metrics)
    df = df[df["roi"] >= STRATEGY_ROI_FILTER]
    df = df.sort_values(by="roi", ascending=False).head(TOP_N)

    if df.empty:
        logger.warning("[PLOT] 시각화할 전략이 없습니다.")
        return

    plt.figure(figsize=(10, 5))
    plt.barh(df["strategy_name"], df["roi"], color="skyblue")
    plt.xlabel("ROI (%)")
    plt.title("Top 전략 ROI")
    plt.gca().invert_yaxis()
    plt.tight_layout()

    graph_path = os.path.join(output_dir, "top_strategies.png")
    plt.savefig(graph_path)
    logger.info(f"[PLOT] ROI 그래프 저장 완료: {graph_path}")

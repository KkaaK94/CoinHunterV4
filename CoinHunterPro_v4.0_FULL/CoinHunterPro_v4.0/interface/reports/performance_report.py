import json
import os
from datetime import datetime
from jinja2 import Template
import plotly.graph_objects as go
import pdfkit

def calculate_cagr(start_value, end_value, periods_per_year, total_periods):
    years = total_periods / periods_per_year
    return (end_value / start_value) ** (1 / years) - 1 if years > 0 else 0.0

def calculate_calmar_ratio(cagr, mdd):
    return cagr / abs(mdd) if mdd != 0 else float("inf")

def calculate_win_rate(win_trades, total_trades):
    return win_trades / total_trades if total_trades > 0 else 0.0

def generate_performance_report(metrics: dict, output_path: str = "interface/reports/strategy_report.html", pdf_output_path: str = "interface/reports/strategy_report.pdf"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    strategy_names = list(metrics.keys())

    # Plotly 그래프
    fig = go.Figure()
    fig.add_trace(go.Bar(x=strategy_names, y=[metrics[k]["total_return"] for k in strategy_names], name="수익률", marker_color='green'))
    fig.add_trace(go.Bar(x=strategy_names, y=[metrics[k]["mdd"] for k in strategy_names], name="MDD", marker_color='red'))
    fig.add_trace(go.Bar(x=strategy_names, y=[metrics[k]["sharpe"] for k in strategy_names], name="샤프비율", marker_color='blue'))
    fig.update_layout(barmode='group', title="📊 전략 성과 비교", xaxis_title="전략명", yaxis_title="지표 값")
    plot_html = fig.to_html(full_html=False, include_plotlyjs='cdn')

    # 지표 보완
    for name, data in metrics.items():
        metrics[name]["win_rate"] = round(calculate_win_rate(data.get("win_trades", 0), data.get("trade_count", 1)), 2)
        metrics[name]["cagr"] = round(calculate_cagr(1, 1 + data.get("total_return", 0), 252, data.get("trade_count", 1)), 4)
        metrics[name]["calmar"] = round(calculate_calmar_ratio(metrics[name]["cagr"], data.get("mdd", 0)), 2)

    html_template = """ ... [동일 - HTML 스타일 및 테이블 코드 생략 가능] ... """
    html = Template(html_template).render(metrics=metrics, timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), plot_html=plot_html)

    with open(output_path, "w") as f:
        f.write(html)
    print(f"[리포트완료] HTML 리포트 생성 → {output_path}")

    if pdf_output_path:
        config = pdfkit.configuration(wkhtmltopdf="/usr/bin/wkhtmltopdf")
        pdfkit.from_file(output_path, pdf_output_path, configuration=config)
        print(f"[PDF 저장완료] PDF 리포트 생성 → {pdf_output_path}")

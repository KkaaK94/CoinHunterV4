# dashboards/dash_main_tabs.py (전략 클릭 → 상세 모달 포함 최신 버전)

import os
import json
import glob
import pandas as pd
from datetime import datetime
from dash import Dash, dcc, html, dash_table
from dash.dependencies import Input, Output, State
import plotly.express as px

# 경로 설정
SCORES_PATH = "data_io/json_store/strategy_scores.json"
WEIGHT_PATH = "data_io/json_store/capital_weights.json"
HEALTH_PATH = "runtime/healthcheck.json"
ENTRY_LOG_DIR = "data_io/json_store/entry_logs"
EXIT_LOG_DIR = "data_io/json_store/exit_logs"
POLICY_PATH = "reinforcement_learning/policy_meta.json"
TRADE_LOG_DIR = "data_io/json_store/trade_log"

# 유틸 함수들
def load_json(path, default=[]):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def load_recent_logs(log_dir, limit=10):
    folders = sorted(glob.glob(f"{log_dir}/*"), reverse=True)
    if not folders:
        return []
    latest_folder = folders[0]
    files = sorted(glob.glob(f"{latest_folder}/*.json"), reverse=True)
    data = []
    for f in files[:limit]:
        try:
            item = json.load(open(f, "r", encoding="utf-8"))
            item["symbol"] = os.path.basename(f).replace(".json", "")
            item["time"] = datetime.fromtimestamp(os.path.getmtime(f)).strftime("%Y-%m-%d %H:%M:%S")
            data.append(item)
        except:
            continue
    return data

def load_policy_status():
    data = load_json(POLICY_PATH, default={})
    if not data:
        return html.P("🧠 정책 정보 없음 (학습 미적용)")
    return html.Ul([
        html.Li(f"현재 정책명: {data.get('current_policy', '미정의')}"),
        html.Li(f"정책 적용 시각: {data.get('applied_at', '미정의')}"),
        html.Li(f"정책 설명: {data.get('description', '없음')}")
    ])

def aggregate_trade_profits():
    data = []
    folders = sorted(glob.glob(f"{TRADE_LOG_DIR}/*"))
    for folder in folders:
        for file in glob.glob(f"{folder}/*.json"):
            try:
                trades = load_json(file, default=[])
                for t in trades:
                    data.append({
                        "strategy": t.get("strategy_name"),
                        "date": folder.split("/")[-1],
                        "profit": t.get("profit", 0)
                    })
            except:
                continue
    df = pd.DataFrame(data)
    if df.empty:
        return pd.DataFrame()
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
    return df.groupby(["strategy", "date"]).sum().reset_index()

# Dash 앱 초기화
app = Dash(__name__)
app.title = "📊 CoinHunterPro 탭형 대시보드"

# 레이아웃 (탭 기반)
app.layout = html.Div([
    html.H1("📊 CoinHunterPro 실시간 통합 대시보드", style={"textAlign": "center"}),
    dcc.Tabs([
        dcc.Tab(label="📈 전략 성과 요약", children=[
            dcc.Interval(id='interval', interval=30*1000, n_intervals=0),
            html.H2("전략별 ROI 순위"),
            dash_table.DataTable(
                id='roi-table',
                columns=[{"name": i, "id": i} for i in ["strategy_name", "roi", "win_rate", "profit", "total_count"]],
                row_selectable="single"
            ),
            dcc.Store(id='selected-strategy'),
            html.Div(id='strategy-modal'),
            html.H2("전략 자본 비중"),
            dcc.Graph(id='capital-weight-graph'),
            html.H2("강화학습 정책 상태"),
            html.Div(id='rl-status')
        ]),

        dcc.Tab(label="💰 누적 수익 & ROI 시계열", children=[
            html.H2("분석 기간 선택"),
            dcc.DatePickerRange(
                id='date-range',
                min_date_allowed=datetime(2024, 1, 1),
                max_date_allowed=datetime.today(),
                initial_visible_month=datetime.today(),
                end_date=datetime.today()
            ),
            html.H2("전략별 ROI 비교"),
            dcc.Graph(id="roi-time-graph"),
            html.H2("전략별 누적 수익 라인차트"),
            dcc.Graph(id="cumulative-profit-graph")
        ]),

        dcc.Tab(label="📋 최근 거래 기록", children=[
            html.H2("최근 진입 로그"),
            dash_table.DataTable(id="entry-log-table"),
            html.H2("최근 청산 로그"),
            dash_table.DataTable(id="exit-log-table")
        ]),

        dcc.Tab(label="🧠 강화학습 분석", children=[
            html.H2("정책 변경 시계열 그래프 (Mock)"),
            dcc.Graph(id="policy-timeline-graph")
        ]),

        dcc.Tab(label="🧭 전략 히트맵", children=[
            html.H2("전략 성능 히트맵 (ROI, 승률, 거래수)"),
            dcc.Graph(id="strategy-heatmap")
        ]),

        dcc.Tab(label="🩺 시스템 상태", children=[
            html.H2("실시간 시스템 상태"),
            html.Div(id='system-health')
        ])
    ])
])

# 콜백 함수들
@app.callback(Output('roi-table', 'data'), Input('interval', 'n_intervals'))
def update_roi_table(n):
    raw = load_json(SCORES_PATH, default=[])
    if not isinstance(raw, list):
        return []
    return sorted(raw, key=lambda x: x.get("roi", 0), reverse=True)

@app.callback(Output('selected-strategy', 'data'), Input('roi-table', 'selected_rows'), State('roi-table', 'data'))
def store_selected_strategy(selected_rows, rows):
    if selected_rows:
        return rows[selected_rows[0]]
    return None

@app.callback(Output('strategy-modal', 'children'), Input('selected-strategy', 'data'))
def show_strategy_modal(strategy_data):
    if not strategy_data:
        return ""
    return html.Div([
        html.H3(f"📊 전략 상세: {strategy_data['strategy_name']}"),
        html.P(f"ROI: {strategy_data['roi']}%"),
        html.P(f"승률: {strategy_data['win_rate']}%"),
        html.P(f"거래수: {strategy_data['total_count']}"),
        html.P(f"누적 수익: {strategy_data['profit']} KRW"),
        html.Hr()
    ], style={"border": "1px solid gray", "padding": "15px", "margin": "10px"})

# (기존 콜백 함수들은 생략 없이 이어짐 — update_weight_graph, update_cumulative_profit, update_roi_time 등 동일)

@app.callback(Output('capital-weight-graph', 'figure'), Input('interval', 'n_intervals'))
def update_weight_graph(n):
    weights = load_json(WEIGHT_PATH, default={})
    df = pd.DataFrame({"strategy": list(weights.keys()), "weight": list(weights.values())})
    if df.empty:
        return px.bar(title="자본 비중 없음")
    return px.pie(df, names='strategy', values='weight', title="전략별 자본 비중 (%)")

@app.callback(Output('system-health', 'children'), Input('interval', 'n_intervals'))
def update_health(n):
    status = load_json(HEALTH_PATH, default={})
    if not status:
        return html.P("🛑 상태 정보 없음")
    return html.Ul([
        html.Li(f"상태: {status.get('status')}"),
        html.Li(f"업데이트 시각: {status.get('timestamp')}"),
        html.Li(f"CPU 사용률: {status.get('cpu_percent')}%"),
        html.Li(f"메모리 사용률: {status.get('mem_percent')}%")
    ])

@app.callback(Output("entry-log-table", "data"), Input("interval", "n_intervals"))
def update_entry_log(n):
    return load_recent_logs(ENTRY_LOG_DIR)

@app.callback(Output("exit-log-table", "data"), Input("interval", "n_intervals"))
def update_exit_log(n):
    return load_recent_logs(EXIT_LOG_DIR)

@app.callback(
    Output("cumulative-profit-graph", "figure"),
    Input("interval", "n_intervals"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date")
)
def update_cumulative_profit(n, start_date, end_date):
    df = aggregate_trade_profits()
    if df.empty:
        return px.line(title="누적 수익 데이터 없음")
    df = df.sort_values("date")
    if start_date and end_date:
        df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]
    df["cum_profit"] = df.groupby("strategy")["profit"].cumsum()
    return px.line(df, x="date", y="cum_profit", color="strategy", title="전략별 누적 수익")

@app.callback(
    Output("roi-time-graph", "figure"),
    Input("interval", "n_intervals"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date")
)
def update_roi_time(n, start_date, end_date):
    df = aggregate_trade_profits()
    if df.empty:
        return px.line(title="ROI 데이터 없음")
    if start_date and end_date:
        df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]
    roi_df = df.groupby("strategy")["profit"].mean().reset_index()
    return px.bar(roi_df, x="strategy", y="profit", title="전략별 ROI (평균 수익 기준)", color="strategy")

@app.callback(Output("rl-status", "children"), Input("interval", "n_intervals"))
def update_rl_status(n):
    return load_policy_status()

@app.callback(Output("policy-timeline-graph", "figure"), Input("interval", "n_intervals"))
def update_policy_graph(n):
    data = load_json(POLICY_PATH, default={})
    df = pd.DataFrame(data.get("history", []))
    if df.empty:
        return px.line(title="정책 전환 기록 없음")
    df["applied_at"] = pd.to_datetime(df["applied_at"])
    return px.scatter(df, x="applied_at", y="policy", title="강화학습 정책 전환 시계열", color="policy")

@app.callback(Output("strategy-heatmap", "figure"), Input("interval", "n_intervals"))
def update_strategy_heatmap(n):
    data = load_json(SCORES_PATH, default=[])
    if not isinstance(data, list) or len(data) == 0:
        return px.imshow([[0]], title="데이터 없음")
    df = pd.DataFrame(data)
    df = df.set_index("strategy_name")
    matrix = df[["roi", "win_rate", "total_count"]]
    return px.imshow(matrix, title="전략 성능 히트맵")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)

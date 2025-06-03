# interface/dashboard/main.py (업그레이드 설계 예시)

import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import json
from pathlib import Path
import plotly.graph_objects as go
from datetime import datetime

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "📊 전략 대시보드"

DATA_PATH = "data_io/json_store"

def load_json_safe(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def render_score_history(score_history):
    fig = go.Figure()
    for name, history in score_history.items():
        fig.add_trace(go.Scatter(x=history["timestamps"], y=history["scores"], mode="lines+markers", name=name))
    fig.update_layout(title="📈 전략 점수 히스토리", xaxis_title="시간", yaxis_title="점수", height=400)
    return dcc.Graph(figure=fig)

def render_scores(scores, alerts_enabled=True):
    cards = []
    for name, score in scores.items():
        color = "danger" if score > 0.8 and alerts_enabled else "primary"
        cards.append(dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H5(name, className="card-title"),
                html.P(f"Score: {score:.2f}", className="card-text"),
                html.Small("🟢 활성" if score > 0.5 else "🔴 비활성")
            ])
        ], color=color, inverse=True), width=3))
    return dbc.Row(cards, className="mb-4")

def render_positions(positions):
    if not positions:
        return html.P("현재 포지션 없음", className="text-muted")
    return dbc.Table([
        html.Thead(html.Tr([html.Th("전략"), html.Th("심볼"), html.Th("수량"), html.Th("진입가"), html.Th("수익률")]))
    ] + [
        html.Tbody([
            html.Tr([
                html.Td(p.get("strategy")),
                html.Td(p.get("symbol")),
                html.Td(p.get("size")),
                html.Td(p.get("entry_price")),
                html.Td(f"{p.get('pnl', 0):.2%}")
            ]) for p in positions
        ])
    ], bordered=True, striped=True, hover=True)

app.layout = dbc.Container([
    html.H1("📈 실시간 전략 모니터링"),
    dbc.Row([
        dbc.Col([
            html.Label("⏱ 갱신 주기 선택"),
            dcc.Dropdown(
                id="interval-dropdown",
                options=[
                    {"label": "1분", "value": 60000},
                    {"label": "5분", "value": 300000},
                    {"label": "10분", "value": 600000}
                ],
                value=60000,
                clearable=False
            )
        ], width=3),
        dbc.Col([
            html.Label("🔍 전략 필터 선택"),
            dcc.Dropdown(id="strategy-filter", multi=True, placeholder="전략 선택")
        ], width=6)
    ]),
    html.Hr(),
    html.H4("🧠 전략 점수 및 상태"),
    html.Div(id="score-display"),
    html.H4("📈 점수 변화 히스토리"),
    html.Div(id="history-display"),
    html.H4("📌 현재 포지션"),
    html.Div(id="position-display"),
    dcc.Interval(id="interval-component", interval=60000, n_intervals=0)
], fluid=True)

@app.callback(
    Output("interval-component", "interval"),
    Input("interval-dropdown", "value")
)
def update_interval(value):
    return value

@app.callback(
    Output("strategy-filter", "options"),
    Output("score-display", "children"),
    Output("history-display", "children"),
    Output("position-display", "children"),
    Input("interval-component", "n_intervals"),
    State("strategy-filter", "value")
)
def update_dashboard(n, selected):
    scores = load_json_safe(f"{DATA_PATH}/strategy_scores.json")
    score_history = load_json_safe(f"{DATA_PATH}/strategy_score_history.json")
    positions = load_json_safe(f"{DATA_PATH}/position_log.json")

    filtered_scores = {k: v for k, v in scores.items() if not selected or k in selected}
    filtered_history = {k: score_history.get(k, {"timestamps": [], "scores": []}) for k in filtered_scores}

    return (
        [{"label": name, "value": name} for name in scores.keys()],
        render_scores(filtered_scores),
        render_score_history(filtered_history),
        render_positions(positions)
    )

if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8050)

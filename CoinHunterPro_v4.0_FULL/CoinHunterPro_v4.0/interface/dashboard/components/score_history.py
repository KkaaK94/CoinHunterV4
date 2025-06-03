# interface/dashboard/components/score_history.py

from dash import dcc
import plotly.graph_objects as go

# 고정된 색상 맵 (필요시 확장 가능)
STRATEGY_COLORS = {
    "Strategy A": "#636EFA",
    "Strategy B": "#EF553B",
    "Strategy C": "#00CC96",
    "Strategy D": "#AB63FA",
    # 기타 전략명 추가 가능
}

def render_score_history(score_history):
    fig = go.Figure()
    for name, history in score_history.items():
        timestamps = history.get("timestamps", [])[-7:]  # 최근 7개만 표시
        scores = history.get("scores", [])[-7:]
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=scores,
            mode="lines+markers",
            name=name,
            line=dict(color=STRATEGY_COLORS.get(name))
        ))
    fig.update_layout(
        title="\ud83d\udcc8 \uc804\ub7b5 \uc810\uc218 \ud788\uc2a4\ud1a0\ub9ac",
        xaxis_title="\uc2dc\uac04",
        yaxis_title="\uc810\uc218",
        height=400
    )
    return dcc.Graph(figure=fig)
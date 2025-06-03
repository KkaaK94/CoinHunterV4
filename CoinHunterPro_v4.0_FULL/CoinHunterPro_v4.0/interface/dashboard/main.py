# interface/dashboard/main.py

import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import json
from pathlib import Path
from dotenv import load_dotenv
import os
import logging

from components.score_cards import render_scores
from components.score_history import render_score_history
from components.position_table import render_positions

# Load environment variables
load_dotenv()

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "\ud83d\udcca \uc804\ub7b5 \ub370\uc2dc\ubcf4\ub4dc"

DATA_PATH = os.getenv("DATA_PATH", "data_io/json_store")

def load_json_safe(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load JSON from {path}: {e}")
        return {}

app.layout = dbc.Container([
    html.H1("\ud83d\udcc8 \uc2e4\uc2dc\uac04 \uc804\ub7b5 \ubaa9\ud45c\uacfc \ud604\ud669"),
    dbc.Row([
        dbc.Col([
            html.Label("\u23f1 \uac31\uc2e0 \uc8fc\uae30 \uc120\ud0dd"),
            dcc.Dropdown(
                id="interval-dropdown",
                options=[
                    {"label": "1\ubd84", "value": 60000},
                    {"label": "5\ubd84", "value": 300000},
                    {"label": "10\ubd84", "value": 600000}
                ],
                value=60000,
                clearable=False
            )
        ], width=3),
        dbc.Col([
            html.Label("\ud83d\udd0d \uc804\ub7b5 \ud544\ud130 \uc120\ud0dd"),
            dcc.Dropdown(id="strategy-filter", multi=True, placeholder="\uc804\ub7b5 \uc120\ud0dd")
        ], width=6)
    ]),
    html.Hr(),
    html.H4("\ud83e\udde0 \uc804\ub7b5 \uc810\uc218 \ubc0f \uc0c1\ud669"),
    html.Div(id="score-display"),
    html.H4("\ud83d\udcc8 \uc810\uc218 \ubcc0\ud654 \ud788\uc2a4\ud1a0\ub9ac"),
    html.Div(id="history-display"),
    html.H4("\ud83d\udccc \ud604\uc7ac \ud3ec\uc9c0\uc158"),
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

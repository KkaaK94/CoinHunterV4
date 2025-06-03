# interface/dashboard/components/score_cards.py

from dash import html
import dash_bootstrap_components as dbc

def render_scores(scores, alerts_enabled=True):
    cards = []
    for name, score in scores.items():
        color = "danger" if score > 0.8 and alerts_enabled else "primary"
        cards.append(dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H5(name, className="card-title"),
                html.P(f"Score: {score:.2f}", className="card-text"),
                html.Small("\ud83d\udfe2 \ud65c\uc131" if score > 0.5 else "\ud83d\udd34 \ube44\ud65c\uc131")
            ])
        ], color=color, inverse=True), width=3))
    return dbc.Row(cards, className="mb-4")

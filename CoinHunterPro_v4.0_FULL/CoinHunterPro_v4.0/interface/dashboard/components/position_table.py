# interface/dashboard/components/position_table.py

from dash import html
import dash_bootstrap_components as dbc

def render_positions(positions):
    if not positions:
        return html.P("\ud604\uc7ac \ud3ec\uc9c0\uc158 \uc5c6\uc74c", className="text-muted")
    return dbc.Table([
        html.Thead(html.Tr([html.Th("\uc804\ub7b5"), html.Th("\uc2ec\xbcf8"), html.Th("\uc218\ub7c9"), html.Th("\uc9c4\uc785\uac00"), html.Th("\uc218\uc775\b960")])),
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

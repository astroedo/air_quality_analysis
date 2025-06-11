"""
Create a pollutant selection dropdown with a label and a div for station count.
"""

from dash import dcc, html

def create_dropdown(pollutants):
    return html.Div([
        html.Label("Seleziona inquinante:"),
        dcc.Loading(
            id="loading-map",
            type="circle",
            children=html.Div([
                dcc.Dropdown(
                    id="pollutant-selector",
                    options=[{"label": p, "value": p} for p in pollutants],
                    value=pollutants[0] if pollutants else None,
                    clearable=False
                ),
                html.Div(id="station-count", style={"marginTop": "10px", "color": "#555"})
            ])
        )
    ], style={
        "position": "absolute",
        "top": "10px",
        "right": "10px",
        "zIndex": 1000,
        "width": "300px",
        "background": "white",
        "padding": "15px",
        "borderRadius": "8px",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.3)"
    })

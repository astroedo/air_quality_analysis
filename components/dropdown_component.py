"""
Create a pollutant selection dropdown with a label and a div for station count.
"""

from dash import dcc, html

def create_dropdown(pollutants, show_all=True):
    if show_all:
        options = [{"label": "Tutti", "value": "Tutti"}] + [{"label": p, "value": p} for p in pollutants]
    else:
        options = [{"label": p, "value": p} for p in pollutants]

    return html.Div([
        html.Label("Select pollutant:"),
        dcc.Loading(
            id="loading-map",
            type="circle",
            children=html.Div([
                dcc.Dropdown(
                    id="pollutant-selector",
                    options=options,
                    value="Tutti",  # Preselezionato
                    clearable=False
                ),
                html.Div(id="station-count", style={"marginTop": "10px", "color": "#555"})
            ])
        )
    ], style={
        "position": "absolute",
        "top": "10px",
        "right": "10px",
        "zIndex": 800,
        "width": "300px",
        "background": "white",
        "padding": "15px",
        "borderRadius": "8px",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.3)"
    })

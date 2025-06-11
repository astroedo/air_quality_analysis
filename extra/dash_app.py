import dash
from dash import dcc, html, Output, Input
import dash_leaflet as dl
import pandas as pd
import requests
import logging

# --- Logging setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Data Fetching ---
def fetch_data(pollutant=None):
    try:
        url = "http://localhost:5000/api/stations"
        if pollutant:
            url += f"?pollutant={pollutant}"
        response = requests.get(url)
        response.raise_for_status()
        return pd.DataFrame(response.json())
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        return pd.DataFrame()

# --- Pollutant list at startup ---
df_all = fetch_data()
pollutants = sorted(df_all["nometiposensore"].dropna().unique()) if not df_all.empty else []

# --- Map Marker Layer ---
def create_layer_group(df, pollutant):
    if df.empty:
        return dl.LayerGroup([], id=f"layer-{pollutant}")
    df_filtered = df[df["nometiposensore"] == pollutant]
    markers = [
        dl.Marker(
            position=[row["lat"], row["lng"]],
            children=dl.Popup([
                html.H4(row['nomestazione']),
                html.P(f"Pollutant: {pollutant}"),
                html.P(f"Coordinates: {row['lat']:.4f}, {row['lng']:.4f}")
            ])
        ) for _, row in df_filtered.iterrows()
    ]
    return dl.LayerGroup(markers, id=f"layer-{pollutant}")

# --- Dash App Initialization ---
app = dash.Dash(__name__)
server = app.server

# --- Layout Styles ---
container_style = {
    "paddingLeft": "40px",
    "paddingRight": "40px",
    "maxWidth": "1200px",
    "margin": "auto"
}
dropdown_card_style = {
    "position": "absolute",
    "top": "10px",
    "right": "10px",
    "zIndex": 1000,
    "width": "300px",
    "background": "white",
    "padding": "15px",
    "borderRadius": "8px",
    "boxShadow": "0 2px 8px rgba(0,0,0,0.3)"
}
spinner_style = {
    "position": "absolute",
    "top": "15px",
    "left": "50%",
    "transform": "translateX(-50%)",
    "zIndex": 1000,
    "backgroundColor": "rgba(255,255,255,0.9)",
    "padding": "10px 20px",
    "borderRadius": "8px",
    "boxShadow": "0 2px 6px rgba(0,0,0,0.2)"
}

# --- App Layout ---
app.layout = html.Div([
    html.Div([
        # Header
        html.H1("Air Quality Monitoring - Lombardia", style={"textAlign": "center"}),
        html.P("Real-time monitoring of air quality stations across Lombardia", style={"textAlign": "center"}),

        # Map and Overlay
        html.Div([
            # Leaflet map
            dl.Map(
                id="map",
                center=[45.5, 9.2],
                zoom=8,
                children=[
                    dl.TileLayer(id="base-layer"),
                    html.Div(id="dynamic-layer")  # dynamic marker layer
                ],
                style={
                    "width": "100%",
                    "height": "600px",  # altezza fissa
                    "margin": "auto",
                    "position": "relative"
                }
            ),

            # Dropdown and station count overlay
            html.Div([
                html.Label("Select Pollutant:"),
                dcc.Loading(
                    id="loading-map",
                    type="circle",
                    fullscreen=False,
                    children=html.Div([
                        dcc.Dropdown(
                            id="pollutant-selector",
                            options=[{"label": pol, "value": pol} for pol in pollutants],
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
        ], style={"position": "relative"}),

        # Footer
        html.Footer("Data source: ARPA Lombardia", style={"textAlign": "center", "fontSize": "12px", "marginTop": "20px"})
    ], style={
        "paddingLeft": "40px",
        "paddingRight": "40px",
        "maxWidth": "1200px",
        "margin": "auto"
    })
])


# --- Callback: Update Map on Pollutant Change ---
@app.callback(
    [Output("map", "children"), Output("station-count", "children")],
    [Input("pollutant-selector", "value")]
)
def update_map(selected_pollutant):
    df = fetch_data(selected_pollutant)
    base_tile = dl.TileLayer(id="base-layer")

    if selected_pollutant and not df.empty:
        layer = create_layer_group(df, selected_pollutant)
        count = df.shape[0]
        return [base_tile, layer], f"{count} stations monitoring '{selected_pollutant}'"
    
    return [base_tile], "No pollutant selected or no data available."

# --- Run App ---
if __name__ == "__main__":
    print("🚀 Running Lombardia Air Quality Dashboard at http://127.0.0.1:8000")
    app.run(debug=True, port=8000)

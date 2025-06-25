import dash
from dash import html, Output, Input
from components.map_component import create_map, create_layer_group
from components.dropdown_component import create_dropdown
from components.fetch_pollutant import fetch_pollutant

dash.register_page(__name__, path="/map", name="Map")

# Precarica i valori per il dropdown
df_all = fetch_pollutant()
pollutants = sorted(df_all["nometiposensore"].dropna().unique()) if not df_all.empty else []

# Layout visualizzazione
layout = html.Div([
    html.H2("Air Quality Map", style={"textAlign": "center"}),
    html.Div([
        create_map(),
        create_dropdown(pollutants),
        html.Div(id="station-count", style={"padding": "10px", "textAlign": "center"})
    ], style={
        "position": "relative",
        "borderRadius": "15px",
        "overflow": "hidden",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.2)"
    })
], style={
    "paddingLeft": "20px",
    "paddingRight": "20px",
    "maxWidth": "1200px",
    "margin": "auto"
})

# Callback per aggiornare i marker
@dash.callback(
    [Output("dynamic-layer", "children"),
     Output("station-count", "children")],
    [Input("pollutant-selector", "value")]
)
def update_map(selected_pollutant):
    # Recupera i dati (filtrati o tutti)
    df = fetch_pollutant(selected_pollutant) if selected_pollutant not in [None, "Tutti"] else fetch_pollutant()

    # Crea layer dei marker
    layer = create_layer_group(df, selected_pollutant)

    # Conteggio stazioni/sensori
    if df.empty:
        return [], "No data."
    
    num_stations = df["nomestazione"].nunique()
    num_sensors = df.shape[0]

    if selected_pollutant and selected_pollutant != "Tutti":
        text = f"Pollutant: '{selected_pollutant}' – {num_stations} stations"
    else:
        text = f"All pollutants – {num_sensors} sensors, {num_stations} stations"

    return layer.children, text

import dash
from dash import html, Output, Input
from components.map_component import create_map, create_layer_group
from components.dropdown_component import create_dropdown
from functions.fetch_pollutant import fetch_pollutant

dash.register_page(__name__, path="/map", name="Mappa")

df_all = fetch_pollutant()
pollutants = sorted(df_all["nometiposensore"].dropna().unique()) if not df_all.empty else []

# Visualization layout
layout = html.Div([
    html.H2("Air Quality Map", style={"textAlign": "center"}),
    html.Div([
        create_map(),
        create_dropdown(pollutants)
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

# Callback to update the map based on selected pollutant
@dash.callback(
    [Output("map", "children"),
     Output("station-count", "children")],
    [Input("pollutant-selector", "value")]
)
def update_map(selected_pollutant):
    df = fetch_pollutant(selected_pollutant)
    base_tile = create_map().children[0]
    if selected_pollutant and not df.empty:
        layer = create_layer_group(df, selected_pollutant)
        return [base_tile, layer], f"{df.shape[0]} stazioni per '{selected_pollutant}'"
    return [base_tile], "Nessun dato disponibile."

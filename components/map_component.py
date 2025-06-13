"""
Create the map component with a dynamic layer group based on selected pollutant.
"""

from dash import html
import dash_leaflet as dl

def create_map():
    return dl.Map(
        id="map",
        center=[45.5, 9.2],
        zoom=8,
        children=[
            dl.TileLayer(id="base-layer", url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"),
            html.Div(id="dynamic-layer")
        ],
        style={
            "width": "100%",
            "height": "600px",
            "margin": "auto",
            "position": "relative",
            "display": "block"
        }
    )

def create_layer_group(df, pollutant):
    if df.empty:
        return dl.LayerGroup([], id=f"layer-{pollutant or 'tutti'}")

    # Filter dataframe by pollutant if specified and not 'Tutti'
    if pollutant and pollutant != "Tutti":
        df = df[df["nometiposensore"] == pollutant]

    # Group by station name and coordinates, aggregate sensors into a list
    grouped = (
        df.groupby(["nomestazione", "lat", "lng"])["nometiposensore"]
        .apply(list)
        .reset_index()
    )

    markers = [
        dl.Marker(
            position=[row["lat"], row["lng"]],
            children=dl.Popup([
                html.H4(row["nomestazione"]),
                html.P(f"Coord: {row['lat']:.4f}, {row['lng']:.4f}"),
                html.P("Inquinanti:"),
                html.Ul([html.Li(p) for p in row["nometiposensore"]])
            ])
        ) for _, row in grouped.iterrows()
    ]

    # Return layer group with markers
    return dl.LayerGroup(markers, id=f"layer-{pollutant or 'tutti'}")


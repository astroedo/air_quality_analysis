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
        return dl.LayerGroup([], id=f"layer-{pollutant}")
    df_filtered = df[df["nometiposensore"] == pollutant]
    markers = [
        dl.Marker(
            position=[row["lat"], row["lng"]],
            children=dl.Popup([
                html.H4(row["nomestazione"]),
                html.P(f"Inquinante: {pollutant}"),
                html.P(f"Coord: {row['lat']:.4f}, {row['lng']:.4f}")
            ])
        ) for _, row in df_filtered.iterrows()
    ]
    return dl.LayerGroup(markers, id=f"layer-{pollutant}")

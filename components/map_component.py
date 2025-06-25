from dash import html
import dash_leaflet as dl
import pandas as pd


def get_static_layers():
    return [
        dl.TileLayer(id="base-layer", url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"),
         
        get_province_layer()  
    ]

def get_regioni_layer():
    """Layer GeoJSON for italian regions"""
    return dl.GeoJSON(
            id="regioni-layer",
            url="https://raw.githubusercontent.com/openpolis/geojson-italy/master/geojson/limits_IT_regions.geojson",
            options=dict(style=dict(fillColor="blue", color="black", weight=2, fillOpacity=0.1)),
            hoverStyle=dict(weight=4, color="red", dashArray=""),
            zoomToBounds=True,
            zoomToBoundsOnClick=True,
        )

def get_province_layer():
    """Layer GeoJSON per le province della Lombardia"""
    return dl.GeoJSON(
        id="province-lombardia-layer",
        url="/assets/province_lombardia.geojson", # Local file for Lombardia provinces
        options=dict(style=dict(color="green", weight=2, fillOpacity=0.05)),
        hoverStyle=dict(color="darkgreen", weight=3),
        zoomToBounds=False
    )

def get_all_province_layer():
    """Layer GeoJSON per le province della Lombardia"""
    return dl.GeoJSON(
        id="province-lombardia-layer",
        url="https://raw.githubusercontent.com/openpolis/geojson-italy/master/geojson/limits_IT_provinces.geojson",
        options=dict(style=dict(color="green", weight=2, fillOpacity=0.05)),
        hoverStyle=dict(color="darkgreen", weight=3),
        zoomToBounds=False  
    )


def create_map():
    """Crea la mappa completa con layer statici iniziali"""
    return dl.Map(
        id="map",
        center=[45.5, 9.2],
        zoom=6,
        children=[
            *get_static_layers(), 
            dl.LayerGroup(id="dynamic-layer") 
        ],
        style={
            "width": "100%",
            "height": "600px",
            "margin": "auto",
            "position": "relative",
            "display": "block"
        }
    )


def create_layer_group(df: pd.DataFrame, pollutant: str):
    """Crea il LayerGroup con i marker delle stazioni filtrate"""
    if df.empty:
        return dl.LayerGroup([], id="dynamic-layer")

    if pollutant and pollutant != "Tutti":
        df = df[df["nometiposensore"] == pollutant]

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
        )
        for _, row in grouped.iterrows()
    ]

    return dl.LayerGroup(markers, id="dynamic-layer")

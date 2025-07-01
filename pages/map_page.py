import dash
import requests
import pandas as pd
from components.logger import logger
from dash import dcc
from dash import html, Output, Input, no_update
from components.dropdown_component import create_dropdown
from components.fetch_pollutant import fetch_pollutant
import plotly.express as px
from datetime import datetime
import geopandas as gpd
import dash_leaflet as dl
import json

province = gpd.read_file('maps/Lombardy_admin2.shp')
province = province.to_crs(epsg=4326)  # Assicurati che sia in WGS84 (lat/lon)

dash.register_page(__name__, path="/map", name="Map")

df_all = fetch_pollutant()
pollutants = sorted(df_all["nometiposensore"].dropna().unique()) if not df_all.empty else []

# Layout aggiornato per includere la legenda
layout = html.Div([
    html.Div(id="redirect-map"),
    html.H2("Air Quality Map", style={"textAlign": "center"}),

    html.Div([  # MAPPA + DROPDOWN + LEGENDA
        html.Div([  # Container mappa
            dl.Map(
                id="leaflet-map",
                center=[45.6997, 9.9276],
                zoom=7,
                children=[
                    dl.TileLayer(id="base-layer"),
                    dl.LayerGroup(id="layer-province")
                ],
                style={"width": "100%", "height": "600px"}
            ),
            create_dropdown(pollutants, show_all=False),
        ], style={"position": "relative"}),
        
        # Legenda posizionata accanto alla mappa
        html.Div(
            id="map-legend",
            style={
                "position": "relative",
                "width": "150px",
                "backgroundColor": "white",
                "border": "2px solid grey",
                "zIndex": "1000",
                "fontSize": "14px",
                "padding": "10px",
                "borderRadius": "5px",
                "display": "none"  # nascosta inizialmente
            }
        )
    ], style={
        "position": "relative",
        "borderRadius": "15px",
        "overflow": "hidden",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.2)",
        "marginBottom": "30px"
    }),

    html.Div([  # DATE + ISTOGRAMMA
        dcc.DatePickerRange(
            id="date-picker-range",
            min_date_allowed=datetime(2020, 1, 1),
            max_date_allowed=datetime(2025, 12, 31),
            start_date=datetime(2024, 12, 1),
            end_date=datetime(2024, 12, 31),
            display_format="YYYY-MM-DD",
            style={
                "border": "1px solid #ccc",
                "borderRadius": "8px",
                "padding": "10px",
                "marginBottom": "20px",
                "backgroundColor": "#ffffff",
                "width": "100%",
                "display": "flex",
                "justifyContent": "center",
                "marginTop": "20px"
            }
        ),
        dcc.Graph(
            id="histogram",
            style={"height": "400px"}
        ),
        html.Div(id='graph-output', style={'textAlign': 'center', 'marginTop': '10px', 'marginBottom': '50px'})
    ])
], style={
    "paddingLeft": "20px",
    "paddingRight": "20px",
    "maxWidth": "1200px",
    "margin": "auto"
})

def fetch_avg_province_pollutant(pollutants, start_date=None, end_date=None):
    """
    Function to fetch pollutant data from the API, filters the data accordingly the time range.
    """
    try:
        if pollutants == "Tutti" or pollutants is None:
            return pd.DataFrame()  # Return empty DataFrame if no pollutant is selected
        if not start_date or not end_date:
            res = requests.get("http://localhost:5001/api/avg_province_time", # if time range not given makes the last 7 days average
                               params={'pollutant': pollutants})
        else:
            res = requests.get("http://localhost:5001/api/avg_province_time", 
                           params = {'pollutant': pollutants,'start_date': start_date, 'end_date': end_date})
        df = pd.DataFrame(res.json())
        return df
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        return pd.DataFrame()

def create_province_layer(df_pollutant):
    nome_to_sigla = {
        "Milano": "MI", "Bergamo": "BG", "Brescia": "BS",
        "Como": "CO", "Cremona": "CR", "Lecco": "LC",
        "Lodi": "LO", "Mantua": "MN", "Monza and Brianza": "MB",
        "Pavia": "PV", "Sondrio": "SO", "Varese": "VA"
    }

    province["sigla"] = province["NAME_2"].map(nome_to_sigla)
    gdf = province.merge(df_pollutant, left_on="sigla", right_on="provincia", how="left")

    # Calcola min e max per la normalizzazione
    min_val = gdf["mean"].min()
    max_val = gdf["mean"].max()

    def get_color(val):
        if pd.isna(val):
            return "#cccccc"  # grigio per assenza dati
        if max_val - min_val < 1e-6:
            norm = 0.5
        else:
            norm = (val - min_val) / (max_val - min_val)
        
        # Scala di colori da verde (basso) a rosso (alto)
        if norm < 0.5:
            # Da verde a giallo
            r = int(255 * norm * 2)
            g = 255
            b = 0
        else:
            # Da giallo a rosso
            r = 255
            g = int(255 * (1 - norm) * 2)
            b = 0
        
        return f"#{r:02x}{g:02x}{b:02x}"

    # Applica i colori
    gdf["color"] = gdf["mean"].apply(get_color)
    gdf["tooltip"] = gdf["NAME_2"] + ": " + gdf["mean"].round(2).astype(str)

    # SOLUZIONE CORRETTA: Crea poligoni individuali con colori personalizzati
    children = []
    
    # Aggiungi TUTTE le province (con e senza dati)
    for _, row in gdf.iterrows():
        # Estrai la geometria per questa provincia
        geom = row["geometry"]
        if geom.geom_type == 'Polygon':
            coords = [[[lat, lon] for lon, lat in geom.exterior.coords]]
        elif geom.geom_type == 'MultiPolygon':
            coords = []
            for poly in geom.geoms:
                coords.append([[lat, lon] for lon, lat in poly.exterior.coords])
        
        # Determina colore e tooltip
        if pd.isna(row["mean"]):
            fill_color = "#cccccc"  # grigio per province senza dati
            tooltip_text = f"{row['NAME_2']}: No data"
        else:
            fill_color = row["color"]
            tooltip_text = f"{row['NAME_2']}: {row['mean']:.2f}"
        
        # Crea un poligono con il colore specifico
        polygon = dl.Polygon(
            positions=coords,
            fillColor=fill_color,
            fillOpacity=0.7,
            color="black",
            weight=1,
            children=[
                dl.Tooltip(
                    children=tooltip_text,
                    permanent=False,
                    sticky=True
                )
            ]
        )
        children.append(polygon)
    
    # Restituisci i poligoni wrappati in un LayerGroup
    return dl.LayerGroup(children=children)

def create_legend(min_val, max_val, get_color_func):
    """Crea gli elementi HTML per la legenda"""
    if pd.isna(min_val) or pd.isna(max_val):
        return []
    
    # Crea 5 valori per la legenda
    legend_values = [min_val + i * (max_val - min_val) / 4 for i in range(5)]
    legend_elements = [html.P("Pollution Level", style={"margin": "0 0 10px 0", "fontWeight": "bold"})]
    
    for val in legend_values:
        color = get_color_func(val)
        legend_elements.append(
            html.Div([
                html.Div(style={
                    "width": "20px",
                    "height": "15px",
                    "backgroundColor": color,
                    "border": "1px solid black",
                    "marginRight": "8px",
                    "display": "inline-block"
                }),
                html.Span(f"{val:.1f}", style={"verticalAlign": "top"})
            ], style={"display": "flex", "alignItems": "center", "margin": "3px 0"})
        )
    
    # Aggiungi "No data"
    legend_elements.append(
        html.Div([
            html.Div(style={
                "width": "20px",
                "height": "15px",
                "backgroundColor": "#cccccc",
                "border": "1px solid black",
                "marginRight": "8px",
                "display": "inline-block"
            }),
            html.Span("No data", style={"verticalAlign": "top"})
        ], style={"display": "flex", "alignItems": "center", "margin": "3px 0"})
    )
    
    return legend_elements

# Callback aggiornato per includere la legenda
@dash.callback(
    [Output("histogram", "figure"),
     Output("histogram", "style"),
     Output("graph-output", "children"),
     Output("layer-province", "children"),
     Output("map-legend", "children"),
     Output("map-legend", "style"),
     Output("redirect-map", "children")],
    [Input("pollutant-selector", "value"),
     Input("date-picker-range", "start_date"),
     Input("date-picker-range", "end_date"),
     Input("session", "data")]
)
def update_all(selected_pollutant, start_date, end_date, session_data):
    """
    Aggiorna mappa, istogramma e legenda basandosi sul pollutant selezionato
    """
    if not session_data or not session_data.get("logged_in"):
        return {}, {'display': 'none'}, "Please login.", [], [], {"display": "none"}, dcc.Location(href="/login", id="redirect-now")
    else:
        try:
            if selected_pollutant == "Tutti" or selected_pollutant is None:
                legend_style = {"display": "none"}
                return {}, {'display': 'none'}, "Please select a pollutant to view the histogram.", [], [], legend_style, no_update
            
            df = fetch_avg_province_pollutant(selected_pollutant, start_date, end_date)
            if df.empty:
                legend_style = {"display": "none"}
                return {}, {'display': 'none'}, "No data available for the selected pollutant and date range.", [], [], legend_style, no_update
            else:
                # Calcola min e max per la legenda
                min_val = df["mean"].min()
                max_val = df["mean"].max()
                
                # Crea il layer della mappa
                layer = create_province_layer(df)
                
                # Crea la legenda
                def get_color(val):
                    if pd.isna(val):
                        return "#cccccc"
                    if max_val - min_val < 1e-6:
                        norm = 0.5
                    else:
                        norm = (val - min_val) / (max_val - min_val)
                    
                    if norm < 0.5:
                        r = int(255 * norm * 2)
                        g = 255
                        b = 0
                    else:
                        r = 255
                        g = int(255 * (1 - norm) * 2)
                        b = 0
                    
                    return f"#{r:02x}{g:02x}{b:02x}"
                
                legend_elements = create_legend(min_val, max_val, get_color)
                legend_style = {
                    "position": "absolute",
                    "bottom": "20px",
                    "left": "20px",
                    "width": "150px",
                    "backgroundColor": "white",
                    "border": "2px solid grey",
                    "zIndex": "1000",
                    "fontSize": "14px",
                    "padding": "10px",
                    "borderRadius": "5px",
                    "display": "block"
                }

                # Crea l'istogramma
                unit = df["unitamisura"].iloc[0] if "unitamisura" in df.columns else ""
                fig = px.bar(
                    df,
                    x="provincia",
                    y="mean", 
                    title=f"Average '{selected_pollutant}' per Province in {unit}",
                    labels={"provincia": "Province", "mean": "Average Value"},
                    template="plotly_white",  
                )
                fig.update_layout(
                    xaxis_title="Province",
                    yaxis_title=f"Average {selected_pollutant} ({unit})",
                    title_x=0.5
                )
                
                return fig, {'display': 'block'}, "", [layer], legend_elements, legend_style, no_update
        
        except Exception as e:
            print("ERRORE CALLBACK:", e)
            legend_style = {"display": "none"}
            return {}, {"display": "none"}, f"Errore: {str(e)}", [], [], legend_style, no_update
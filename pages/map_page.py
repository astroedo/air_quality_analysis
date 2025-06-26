import dash
import requests
import pandas as pd
from components.logger import logger
from dash import dcc
from dash import html, Output, Input
from components.map_component import create_map, create_layer_group
from components.dropdown_component import create_dropdown
from components.fetch_pollutant import fetch_pollutant
import plotly.express as px
from datetime import datetime, timedelta

dash.register_page(__name__, path="/map", name="Map")

df_all = fetch_pollutant()
pollutants =  sorted(df_all["nometiposensore"].dropna().unique()) if not df_all.empty else []

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
    }),html.Div([

    dcc.DatePickerRange( # DatePickerRange component, calendar for selecting a date range
        id="date-picker-range",
        min_date_allowed=datetime(2024, 1, 1),
        max_date_allowed=datetime(2025, 1, 1),
        start_date_placeholder_text="Start Period",
        end_date_placeholder_text="End Period",
        calendar_orientation='vertical',
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
    dcc.Graph( # Histogram component, bar chart for average pollutant values per province
        id="histogram",
        style={"height": "400px"}
    ),
    html.Div(id='graph-output', style={'textAlign': 'center',  'marginTop': '10px', 'marginBottom': '50px'}),
    ])  
    ], style={
    "paddingLeft": "20px",
    "paddingRight": "20px",
    "maxWidth": "1200px",
    "margin": "auto"})

# Callback to update the map based on selected pollutant
@dash.callback(
    [Output("map", "children"),
     Output("station-count", "children")],
    [Input("pollutant-selector", "value")]
)
def update_map(selected_pollutant):
    base_tile = create_map().children[0]

    if selected_pollutant in [None, "Tutti"]:
        df = fetch_pollutant()  # Nessun filtro
        num_sensors = df.shape[0]
        num_stations = df["nomestazione"].nunique()
        layer = create_layer_group(df, selected_pollutant)
        count_text = f"All pollutants – {num_sensors} sensors, {num_stations} stations"
        return [base_tile, layer], count_text

    else:
        df = fetch_pollutant(selected_pollutant)
        pollutant_label = f"Pollutant: '{selected_pollutant}'"
        layer = create_layer_group(df, selected_pollutant)
        if not df.empty:
            num_stations = df["nomestazione"].nunique()
            count_text = f"{pollutant_label} – {num_stations} stations"
        else:
            count_text = "No data."
        return [base_tile, layer], count_text


# ------ HISTOGRAM FUNCTIONS ------

def fetch_avg_province_pollutant(pollutants, start_date=None, end_date=None):
    """
    Function to fetch pollutant data from the API, filters the data accordingly the time range.
    """
    try:
        if pollutants == "Tutti" or pollutants is None:
            return pd.DataFrame()  # Return empty DataFrame if no pollutant is selected
        if not start_date or not end_date:
            res = requests.get("http://localhost:5000/api/avg_province_time",
                               params={'pollutant': pollutants})
        else:
            res = requests.get("http://localhost:5000/api/avg_province_time", 
                           params = {'pollutant': pollutants,'start_date': start_date, 'end_date': end_date})
        df = pd.DataFrame(res.json())
        return df
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        return pd.DataFrame()

# Callback to update the histogram based on selected pollutant and date range
@dash.callback(
    [Output("histogram",  "figure"),
     Output("histogram", "style"),
     Output("graph-output", "children")],
    [Input("pollutant-selector", "value"),
     Input("date-picker-range", "start_date"),
     Input("date-picker-range", "end_date")]
)
def update_histogram(selected_pollutant, start_date, end_date):
    """
    Creates a histogram (bar chart) of average pollutant values per province.
    """
    if selected_pollutant == "Tutti" or selected_pollutant is None:
        return ({},{'display': 'none'}, "Please select a pollutant to view the histogram.")
    df = fetch_avg_province_pollutant(selected_pollutant, start_date, end_date)
    if df.empty:
        return ({},{'display': 'none'}, "No data available for the selected pollutant and date range.")
    else:
        unit = df["unitamisura"].iloc[0] if "unitamisura" in df.columns else "" # retrieve unit of measurement
        fig = px.bar( # bar chart creation
            df,
            x="provincia",
            y="mean", 
            title=f"Average '{selected_pollutant}' per Province in {unit}",
            labels={"provincia": "Province", "mean": "Average Value"},
            template="plotly_white",  
        )
        fig.update_layout( # axis and title configuration 
            xaxis_title="Province",
            yaxis_title=f"Average {selected_pollutant} ({unit})",
            title_x=0.5)
        return (fig, {'display': 'block'}, "")
    
    


    

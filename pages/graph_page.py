import dash
from dash import html, dcc, Output, Input, callback, no_update
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import psycopg2
from datetime import datetime, timedelta
from components.fetch_pollutant import fetch_pollutant
import numpy as np
import requests
from components.logger import logger



# Register the page
dash.register_page(__name__, path="/trend", name="Trends")



# Fetch initial data for dropdowns
df_all = fetch_pollutant()
pollutants = sorted(df_all["nometiposensore"].dropna().unique()) if not df_all.empty else []
stations = sorted(df_all["nomestazione"].dropna().unique()) if not df_all.empty else []

def get_idsensore(df, nometiposensore=None, nomestazione=None):
    # print("DataFrame:", df.columns.tolist())  # check columns in the DataFrame
    filtered_df = df

    if nometiposensore is not None:
        filtered_df = filtered_df[filtered_df['nometiposensore'] == nometiposensore]

    if nomestazione is not None:
        filtered_df = filtered_df[filtered_df['nomestazione'] == nomestazione]

    # obtain unique idsensore values
    idsensori = filtered_df['idsensore'].unique()

    return idsensori.tolist()


def fetch_sensor_data_api(idsensore=None, datainizio=None, datafine=None):
    """
    Fetch sensor data from the /api/measurements endpoint,
    returning a DataFrame with columns similar to the sample fetch_sensor_data function.
    """

    try:
        url = "http://localhost:5001/api/measurements"
        params = {}

        if idsensore:
            params['idsensore'] = idsensore
        if datainizio:
            params['datainizio'] = datainizio
        if datafine:
            params['datafine'] = datafine

        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()

        if not data:
            return pd.DataFrame()

        # build DataFrame
        df = pd.DataFrame(data)

        df['nometiposensore'] = df.get('idsensore', None)

        ### check what appened if nomestazione as no pollutant related value 
        if 'nomestazione' not in df.columns:
            df['nomestazione'] = None

        # order by 'data' if it exists
        if 'data' in df.columns:
            df['data'] = pd.to_datetime(df['data'])
            df = df.sort_values('data')

        logger.info("Sensor data fetched successfully")

        return df[['data', 'valore', 'nomestazione', 'nometiposensore', 'stato']]

    except Exception as e:
        print(f"Error fetching sensor data from API: {e}")
        return pd.DataFrame()


# Get provinces for NOx analysis
def get_provinces():
    try:
        response = requests.get("http://localhost:5001/api/provinces")
        response.raise_for_status()  # check for HTTP errors
        data = response.json()
        
        # transform the list of provinces into a DataFrame
        df = pd.DataFrame(data, columns=["provincia"])
        
        logger.info("Provinces fetched successfully")
        # Rimuove eventuali NaN e ritorna la lista
        return df["provincia"].dropna().tolist()
    
    except requests.RequestException as e:
        print(f"Errore API: {e}")
        return []
    except Exception as e:
        print(f"Errore imprevisto: {e}")
        return []


# Fetch NOx data from the API       
def fetch_nox_data(pollutant, province=None, time_period="full", datainizio=None, datafine=None):
    """Fetch NOx data calling the API measurements_by_province"""

    if pollutant == "NO":
        pollutant = "Monossido di Azoto"
    elif pollutant == "NO2":
        pollutant = "Biossido di Azoto"

    # build the query parameters
    params = {
        "pollutant": pollutant,
    }
    if province:
        params["provincia"] = province
    if datainizio:
        params["datainizio"] = datainizio
    if datafine:
        params["datafine"] = datafine

    try:
        url = "http://localhost:5001/api/measurements_by_province"

        response = requests.get(url, params=params)
        response.raise_for_status()  

        data = response.json()

        if not data:
            print('No data found for the specified filters.')
            return pd.DataFrame()

        # DataFrame
        df = pd.DataFrame(data)

        df["data"] = pd.to_datetime(df["data"])
        df["valore"] = pd.to_numeric(df["valore"], errors="coerce")
        df = df.dropna()
        df.sort_values("data", inplace=True)
        df["smoothed"] = df["valore"].rolling(window=7, min_periods=1).mean()

        # Filter time_period
        if time_period == "first":
            df = df[df["data"].dt.month <= 6]
        elif time_period == "second":
            df = df[df["data"].dt.month > 6]

        logger.info(f"Data fetched successfully -> pollutant: '{pollutant}', province: '{province}' ")

        return df

    except requests.RequestException as e:
        print(f"Errore nella chiamata API: {e}")
        return pd.DataFrame()
    except Exception as e:
        print(f"Errore imprevisto: {e}")
        return pd.DataFrame()




# Pollutant categories 
# NOx categories
def get_nox_categories():
    return ["NO", "NO2", "Ossidi di Azoto"]

# Time period options
def get_time_period_options():
    return [
        {"label": "First Half Year (Jan-Jun)", "value": "first"},
        {"label": "Second Half Year (Jul-Dec)", "value": "second"},
        {"label": "Full Year", "value": "full"}
    ]

# Data smoothing options
def get_smoothing_options():
    return [
        {"label": "Raw Data", "value": "raw"},
        {"label": "7-day Average", "value": "smoothed"}
    ]

def create_nox_chart(df, pollutant, province, smoothing="raw"):
    """Create NOx analysis chart"""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No NOx data available for the selected filters",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(
            title="No NOx Data Available",
            height=400
        )
        return fig
    
    y_data = df["valore"] if smoothing == "raw" else df["smoothed"]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["data"],
        y=y_data,
        mode="lines+markers",
        line=dict(color="DarkOrange", width=3),
        marker=dict(size=5, color="DarkOrange"),
        name=f"{pollutant} ({province})"
    ))
    
    fig.update_layout(
        title=f"{pollutant} Concentration in {province} - 2024",
        xaxis_title="Date",
        yaxis_title="Concentration (μg/m³)",
        template="plotly_white",
        hovermode="x unified",
        height=500,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    return fig



def create_trend_chart(df, pollutant, station):
    """Create a time series chart for the selected data"""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available for the selected filters",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(
            title="No Data Available",
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False),
            height=400
        )
        return fig

    fig = px.line(
        df, 
        x='data', 
        y='valore',
        title=f"{pollutant} Levels at {station}",
        labels={
            'data': 'Date',
            'valore': f'{pollutant} Concentration (μg/m³)'
        }
    )
    
    fig.update_layout(
        title=dict(
            text=f"{pollutant} Trends - {station}",
            x=0.5,
            font=dict(size=20, color="rgb(19, 129, 159)")
        ),
        xaxis=dict(
            title="Date",
            gridcolor="lightgray",
            showgrid=True
        ),
        yaxis=dict(
            title=f"{pollutant} Concentration (μg/m³)",
            gridcolor="lightgray",
            showgrid=True
        ),
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=500,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    fig.update_traces(
        line=dict(color="rgb(19, 129, 159)", width=2),
        hovertemplate="<b>%{x}</b><br>" +
                     f"{pollutant}: %{{y:.2f}} μg/m³<br>" +
                     "<extra></extra>"
    )
    
    return fig



def create_summary_cards(df, pollutant):
    """Create summary statistics cards"""
    if df.empty:
        return html.Div("No data available", style={"textAlign": "center", "color": "gray"})
    
    avg_value = df['valore'].mean()
    max_value = df['valore'].max()
    min_value = df['valore'].min()
    data_points = len(df)
    
    cards = html.Div([
        # Average Card
        html.Div([
            html.H4("Average", style={"margin": "0", "color": "rgb(19, 129, 159)"}),
            html.H2(f"{avg_value:.1f}", style={"margin": "5px 0", "color": "#2c3e50"}),
            html.P("μg/m³", style={"margin": "0", "color": "gray", "fontSize": "14px"})
        ], style={
            "backgroundColor": "white",
            "padding": "20px",
            "borderRadius": "10px",
            "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
            "textAlign": "center",
            "flex": "1",
            "margin": "0 10px"
        }),
        
        # Maximum Card
        html.Div([
            html.H4("Maximum", style={"margin": "0", "color": "rgb(231, 76, 60)"}),
            html.H2(f"{max_value:.1f}", style={"margin": "5px 0", "color": "#2c3e50"}),
            html.P("μg/m³", style={"margin": "0", "color": "gray", "fontSize": "14px"})
        ], style={
            "backgroundColor": "white",
            "padding": "20px",
            "borderRadius": "10px",
            "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
            "textAlign": "center",
            "flex": "1",
            "margin": "0 10px"
        }),
        
        # Minimum Card
        html.Div([
            html.H4("Minimum", style={"margin": "0", "color": "rgb(46, 204, 113)"}),
            html.H2(f"{min_value:.1f}", style={"margin": "5px 0", "color": "#2c3e50"}),
            html.P("μg/m³", style={"margin": "0", "color": "gray", "fontSize": "14px"})
        ], style={
            "backgroundColor": "white",
            "padding": "20px",
            "borderRadius": "10px",
            "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
            "textAlign": "center",
            "flex": "1",
            "margin": "0 10px"
        }),
        
        # Data Points Card
        html.Div([
            html.H4("Data Points", style={"margin": "0", "color": "rgb(155, 89, 182)"}),
            html.H2(f"{data_points}", style={"margin": "5px 0", "color": "#2c3e50"}),
            html.P("readings", style={"margin": "0", "color": "gray", "fontSize": "14px"})
        ], style={
            "backgroundColor": "white",
            "padding": "20px",
            "borderRadius": "10px",
            "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
            "textAlign": "center",
            "flex": "1",
            "margin": "0 10px"
        })
    ], style={
        "display": "flex",
        "justifyContent": "space-between",
        "margin": "20px 0"
    })
    
    return cards

# Layout
layout = html.Div([
    html.Div(id="redirect-trend"),
    # Page Header
    html.Div([
        html.H1("📈 Air Quality Trends Analysis", style={
            "textAlign": "center",
            "color": "rgb(19, 129, 159)",
            "marginBottom": "10px",
            "fontSize": "32px"
        }),
        html.P("Analyze temporal patterns in air quality measurements with specialized NOx analysis", style={
            "textAlign": "center",
            "color": "#7f8c8d",
            "fontSize": "16px",
            "marginBottom": "30px"
        })
    ]),
    
    # Analysis Mode Selector
    html.Div([
        html.H3("🔬 Select Analysis Mode", style={"color": "#2c3e50", "marginBottom": "15px"}),
        dcc.RadioItems(
            id="analysis-mode",
            options=[
                {"label": " General Pollutant Analysis", "value": "general"},
                {"label": " NOx Specialized Analysis", "value": "nox"}
            ],
            value="general",
            style={"fontSize": "16px"},
            labelStyle={"margin": "10px", "display": "block"}
        )
    ], style={
        "backgroundColor": "white",
        "padding": "20px",
        "borderRadius": "10px",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
        "margin": "0 20px 20px 20px"
    }),
    
    # General Analysis Controls
    html.Div(id="general-controls", children=[
        html.Div([
            html.Div([
                html.Label("🔬 Select Pollutant:", style={
                    "fontWeight": "bold",
                    "marginBottom": "8px",
                    "display": "block",
                    "color": "#2c3e50"
                }),
                dcc.Dropdown(
                    id="trend-pollutant-selector",
                    options=[{"label": pol, "value": pol} for pol in pollutants],
                    value=pollutants[0] if pollutants else None,
                    clearable=False,
                    style={"marginBottom": "20px"}
                )
            ], style={"flex": "1", "marginRight": "20px"}),
            
            html.Div([
                html.Label("🏭 Select Station:", style={
                    "fontWeight": "bold",
                    "marginBottom": "8px",
                    "display": "block",
                    "color": "#2c3e50"
                }),
                dcc.Dropdown(
                    id="trend-station-selector",
                    options=[{"label": station, "value": station} for station in stations],
                    value=stations[0] if stations else None,
                    clearable=False,
                    style={"marginBottom": "20px"}
                )
            ], style={"flex": "1"})
        ], style={"display": "flex"})
    ], style={
        "backgroundColor": "white",
        "padding": "20px",
        "borderRadius": "10px",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
        "margin": "0 20px 20px 20px"
    }),
    
    # NOx Analysis Controls
    html.Div(id="nox-controls", children=[
        html.Div([
            html.Div([
                html.Label("🏢 Select Province:", style={
                    "fontWeight": "bold",
                    "marginBottom": "8px",
                    "display": "block",
                    "color": "#2c3e50"
                }),
                dcc.Dropdown(
                    id="nox-province-selector",
                    options=[{"label": p, "value": p} for p in get_provinces()],
                    value="Milano",
                    clearable=False
                )
            ], style={"flex": "1", "marginRight": "15px"}),
            
            html.Div([
                html.Label("🧪 NOx Category:", style={
                    "fontWeight": "bold",
                    "marginBottom": "8px",
                    "display": "block",
                    "color": "#2c3e50"
                }),
                dcc.Dropdown(
                    id="nox-pollutant-selector",
                    options=[{"label": p, "value": p} for p in get_nox_categories()],
                    value="NO2",
                    clearable=False
                )
            ], style={"flex": "1", "marginRight": "15px"}),
            
            html.Div([
                html.Label("📅 Time Period:", style={
                    "fontWeight": "bold",
                    "marginBottom": "8px",
                    "display": "block",
                    "color": "#2c3e50"
                }),
                dcc.Dropdown(
                    id="nox-time-period",
                    options=get_time_period_options(),
                    value="full",
                    clearable=False
                )
            ], style={"flex": "1", "marginRight": "15px"}),
            
            html.Div([
                html.Label("📊 Data Smoothing:", style={
                    "fontWeight": "bold",
                    "marginBottom": "8px",
                    "display": "block",
                    "color": "#2c3e50"
                }),
                dcc.Dropdown(
                    id="nox-smoothing",
                    options=get_smoothing_options(),
                    value="raw",
                    clearable=False
                )
            ], style={"flex": "1"})
        ], style={"display": "flex"})
    ], style={
        "backgroundColor": "white",
        "padding": "20px",
        "borderRadius": "10px",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
        "margin": "0 20px 20px 20px",
        "display": "none"
    }),
    
    # Summary Cards
    html.Div(id="summary-cards", style={"margin": "0 20px"}),
    
    # Chart Container
    html.Div([
        
        dcc.Graph(
            id="trend-chart",
            config={
                'displayModeBar': True,
                'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
                'displaylogo': False
            }
        )
    ], style={
        "backgroundColor": "white",
        "margin": "20px",
        "borderRadius": "10px",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
        "padding": "10px"
    }),
    
    # Footer Info
    html.Div([
        html.P("💡 Tip: Switch between General and NOx analysis modes to explore different aspects of air quality data.", style={
            "textAlign": "center",
            "color": "#95a5a6",
            "fontSize": "14px",
            "fontStyle": "italic",
            "margin": "20px"
        })
    ])
], style={
    "maxWidth": "1200px",
    "margin": "auto",
    "padding": "20px 0"
})

# Callback to show/hide controls based on analysis mode
@callback(
    [Output("general-controls", "style"),
     Output("nox-controls", "style")],
    [Input("analysis-mode", "value")]
)
def toggle_controls(mode):
    
    if mode == "general":
        return {"backgroundColor": "white", "padding": "20px", "borderRadius": "10px", 
                "boxShadow": "0 2px 8px rgba(0,0,0,0.1)", "margin": "0 20px 20px 20px"}, \
            {"display": "none"}
    else:
        return {"display": "none"}, \
            {"backgroundColor": "white", "padding": "20px", "borderRadius": "10px", 
                "boxShadow": "0 2px 8px rgba(0,0,0,0.1)", "margin": "0 20px 20px 20px"}

# Callback to update station options based on selected pollutant (for general analysis)
@callback(
    Output("trend-station-selector", "options"),
    Input("trend-pollutant-selector", "value")
)
def update_station_options(selected_pollutant):
    """Update available stations based on selected pollutant"""
    if not selected_pollutant:
        return []

    # Fetch data already filtered by pollutant
    df_filtered = fetch_pollutant(pollutant=selected_pollutant)
    
    # Extract unique station names
    available_stations = sorted(df_filtered["nomestazione"].dropna().unique())

    return [{"label": station, "value": station} for station in available_stations]

# Main callback to update chart and summary
@callback(
    [Output("trend-chart", "figure"),
     Output("summary-cards", "children"),
     Output("redirect-trend", "children")],
    [Input("analysis-mode", "value"),
     Input("trend-pollutant-selector", "value"),
     Input("trend-station-selector", "value"),
     Input("nox-province-selector", "value"),
     Input("nox-pollutant-selector", "value"),
     Input("nox-time-period", "value"),
     Input("nox-smoothing", "value"),
     Input("session", "data")]
)
def update_chart_and_summary(mode, pollutant, station, province, nox_pollutant, time_period, smoothing, session_data):
    """Update the chart and summary based on selected analysis mode and parameters"""
    if not session_data or not session_data.get("logged_in"):
        fig = go.Figure()
        fig.add_annotation(
            text="Redirecting to login...",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(height=300)
        return fig, "", dcc.Location(href="/login", id="redirect-now")
    else:
        if mode == "general":
            # General pollutant analysis
            if not pollutant or not station:
                empty_fig = go.Figure()
                empty_fig.add_annotation(
                    text="Please select both pollutant and station",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, xanchor='center', yanchor='middle',
                    showarrow=False,
                    font=dict(size=16, color="gray")
                )
                empty_fig.update_layout(
                    title="Select Filters",
                    height=400,
                    xaxis=dict(showgrid=False, showticklabels=False),
                    yaxis=dict(showgrid=False, showticklabels=False)
                )
                empty_summary = html.Div("Select pollutant and station to view summary", 
                                    style={"textAlign": "center", "color": "gray", "padding": "20px"})
                return empty_fig, empty_summary, no_update
            
            # Fetch sensor data for the selected combination
            # df_sensor = fetch_sensor_data(pollutant, station)          # old
            id_sensore = get_idsensore(df_all, pollutant, station)
            df_sensor = fetch_sensor_data_api(id_sensore)
            
            # Create chart and summary
            fig = create_trend_chart(df_sensor, pollutant, station)
            summary = create_summary_cards(df_sensor, pollutant)
            
        else:
            # NOx specialized analysis
            # print(f"--> Fetching NOx data for {province}, {nox_pollutant}, {time_period}, smoothing: {smoothing} \n\n")
            df_nox = fetch_nox_data(nox_pollutant, province, time_period)
            fig = create_nox_chart(df_nox, nox_pollutant, province, smoothing)
            summary = create_summary_cards(df_nox, nox_pollutant)
        
        return fig, summary, no_update
















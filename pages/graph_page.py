import dash
from dash import html, dcc, Output, Input, callback, no_update
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
from components.fetch_pollutant import fetch_pollutant
import numpy as np
import requests
from components.logger import logger



# Register the page
dash.register_page(__name__, path="/trend", name="Trends")



# Fetch initial data for dropdown menus
df_all = fetch_pollutant()
# Get sorted list of unique pollutant types if data is available
pollutants = sorted(df_all["nometiposensore"].dropna().unique()) if not df_all.empty else []
# Get sorted list of unique stations if data is available
stations = sorted(df_all["nomestazione"].dropna().unique()) if not df_all.empty else []

def get_idsensore(df, nometiposensore=None, nomestazione=None):
    # Filter the dataframe based on pollutant type and/or station name if provided
    filtered_df = df

    if nometiposensore is not None:
        filtered_df = filtered_df[filtered_df['nometiposensore'] == nometiposensore]

    if nomestazione is not None:
        filtered_df = filtered_df[filtered_df['nomestazione'] == nomestazione]

    # Return list of unique sensor IDs after filtering
    idsensori = filtered_df['idsensore'].unique()

    return idsensori.tolist()


def fetch_sensor_data_api(idsensore=None):
    """
    Fetch sensor measurement data from the API endpoint,
    returning a DataFrame with relevant columns.
    """
    try:
        url = "http://localhost:5001/api/measurements"
        params = {}

        # Add parameters if provided for sensor ID and date range
        if idsensore:
            params['idsensore'] = idsensore

        # Call the API and check response status
        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()

        # Return empty DataFrame if no data
        if not data:
            return pd.DataFrame()

        # Create DataFrame from JSON data
        df = pd.DataFrame(data)

        # Assign pollutant type column based on sensor ID (fallback)
        df['nometiposensore'] = df.get('idsensore', None)

        # Ensure 'nomestazione' column exists
        if 'nomestazione' not in df.columns:
            df['nomestazione'] = None

        # Convert 'data' column to datetime and sort if exists
        if 'data' in df.columns:
            df['data'] = pd.to_datetime(df['data'])
            df = df.sort_values('data')

        logger.info("Sensor data fetched successfully")

        # Return selected columns
        return df[['data', 'valore', 'nomestazione', 'nometiposensore', 'stato']]

    except Exception as e:
        logger.error(f"Error fetching sensor data from API: {e}")
        return pd.DataFrame()


# Get list of provinces from API for analysis
def get_provinces():
    try:
        response = requests.get("http://localhost:5001/api/provinces")
        response.raise_for_status()  # Raise error for bad HTTP responses
        data = response.json()
        
        # Convert list to DataFrame
        df = pd.DataFrame(data, columns=["provincia"])
        
        logger.info("Provinces fetched successfully")
        # Return cleaned list of provinces without NaNs
        return df["provincia"].dropna().tolist()
    
    except requests.RequestException as e:
        logger.error(f"API Error: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return []


# Fetch measurements data filtered by pollutant and optionally province and date range
def fetch_data(pollutant, province=None, start_date=None, end_date=None):
    """Fetch data calling the API endpoint for measurements filters"""

    # Prepare query parameters for API call
    params = {
        "pollutant": pollutant,
    }
    if province:
        params["provincia"] = province
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date

    try:
        url = "http://localhost:5001/api/measurements_filters"

        # Make GET request and check for errors
        response = requests.get(url, params=params)
        response.raise_for_status()  

        data = response.json()

        # Handle empty response
        if not data:
            logger.warning(f"NO DATA found for pollutant: '{pollutant}', province: '{province}', start_date: '{start_date}', end_date: '{end_date}' ")
            return pd.DataFrame()

        # Convert to DataFrame and clean data
        df = pd.DataFrame(data)
        df["data"] = pd.to_datetime(df["data"])
        df["valore"] = pd.to_numeric(df["valore"], errors="coerce")
        df = df.dropna()
        df.sort_values("data", inplace=True)
        # Calculate 7-day rolling average for smoothing
        df["smoothed"] = df["valore"].rolling(window=7, min_periods=1).mean()

        logger.info(f"Fetched successfully -> pollutant: '{pollutant}', province: '{province}', start_date: '{start_date}', end_date: '{end_date}'  ")

        return df

    except requests.RequestException as e:
        logger.error(f"API call error: {e}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return pd.DataFrame()


# Fetch data for multiple pollutants combined into a single DataFrame
def fetch_data_multiple(pollutants, province, start_date=None, end_date=None):
    df_list = []
    for pol in pollutants:
        df = fetch_data(pol, province, start_date, end_date)
        df["pollutant"] = pol
        df_list.append(df)
    # Concatenate all dataframes if any, else return empty
    return pd.concat(df_list, ignore_index=True) if df_list else pd.DataFrame()


# Options for data smoothing methods for visualization
def get_smoothing_options():
    return [
        {"label": "Daily average", "value": "raw"},
        {"label": "7-day average", "value": "smoothed_7"},
        {"label": "14-day average", "value": "smoothed_14"}
    ]


# Create a line chart for a single pollutant in a province with optional smoothing
def create_nox_chart(df, pollutant, province, smoothing="raw"):
    """Create NOx analysis chart"""
    if df.empty:
        # Return placeholder figure if no data
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
            height=400
        )
        return fig
    
    # Select data column based on smoothing choice
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
    
    # Set layout properties for better visualization
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


# Create line chart for multiple pollutants in a province with smoothing options
def create_nox_chart_multi(df, smoothing="raw", province=None):
    if df.empty:
        # Placeholder figure when no data available
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
            height=400
        )
        return fig

    # Add a column selecting raw or smoothed values for y-axis
    df["y"] = df["valore"] if smoothing == "raw" else df["smoothed"]

    fig = go.Figure()

    # Add a separate trace for each pollutant
    for pollutant in df["pollutant"].unique():
        sub_df = df[df["pollutant"] == pollutant]

        fig.add_trace(go.Scatter(
            x=sub_df["data"],
            y=sub_df["y"],
            mode="lines+markers",
            name=pollutant,
            line=dict(width=2),
            marker=dict(size=4),
            hovertemplate = "<b>%{x|%Y-%m-%d}</b><br>" + f"{pollutant}: %{{y:.2f}} μg/m³<extra></extra>"
        ))

    fig.update_layout(
        title=f"Pollutants in {'All Provinces' if not province else province}",
        xaxis_title="Date",
        yaxis_title="Concentration (μg/m³)",
        template="plotly_white",
        hovermode="x unified",
        height=500,
        margin=dict(l=50, r=50, t=80, b=50)
    )

    return fig


# Create a time series trend chart for a specific pollutant at a station
def create_trend_chart(df, pollutant, station):
    """Create a time series chart for the selected data"""
    if df.empty:
        # Show placeholder figure when no data
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

    # Use Plotly Express for quick line plot creation
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
    
    # Customize layout for clarity and style
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
    
    # Style line and hover tooltip
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


def create_summary_cards_per_pollutant(df, pollutants):
    """Create summary cards for multiple pollutants"""
    if df.empty:
        return html.Div("No data available", style={"textAlign": "center", "color": "gray"})

    cards = []

    # Se è stringa singola, converti in lista
    if isinstance(pollutants, str):
        pollutants = [pollutants]

    for pollutant in pollutants:
        sub_df = df[df["pollutant"] == pollutant]
        if sub_df.empty:
            continue

        avg_value = sub_df["valore"].mean()
        max_value = sub_df["valore"].max()
        min_value = sub_df["valore"].min()
        data_points = len(sub_df)

        cards.append(html.Div([
            html.H4(pollutant, style={"margin": "0", "color": "#2c3e50"}),
            html.P(f"Average: {avg_value:.1f} μg/m³", style={"margin": "4px 0", "color": "rgb(19, 129, 159)"}),
            html.P(f"Max: {max_value:.1f} μg/m³", style={"margin": "4px 0", "color": "rgb(231, 76, 60)"}),
            html.P(f"Min: {min_value:.1f} μg/m³", style={"margin": "4px 0", "color": "rgb(46, 204, 113)"}),
            html.P(f"Data Points: {data_points}", style={"margin": "4px 0", "color": "#7f8c8d", "fontSize": "13px"})
        ], style={
            "backgroundColor": "white",
            "padding": "15px",
            "borderRadius": "10px",
            "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
            "textAlign": "center",
            "minWidth": "180px",
            "flex": "1",
            "margin": "10px"
        }))

    return html.Div(cards, style={
        "display": "flex",
        "flexWrap": "wrap",
        "justifyContent": "center",
        "gap": "10px",
        "margin": "20px 0"
    })






### LAYOUT -> TRENDS PAGE ###
layout = html.Div([
    html.Div(id="redirect-trend"),
    # Page Header
    html.Div([
        html.H1("Air Quality Trends Analysis", style={
            "textAlign": "center",
            "color": "rgb(19, 129, 159)",
            "marginBottom": "10px",
            "fontSize": "32px"
        }),
        html.P("Analyze temporal patterns for each station in Lombardy region or compare the different pollutant with the specialized analysis", style={
            "textAlign": "center",
            "color": "#7f8c8d",
            "fontSize": "16px",
            "marginBottom": "30px"
        })
    ]),
    
    # Analysis Mode Selector
    html.Div([
        html.H3("Select Analysis Mode", style={"color": "#2c3e50", "marginBottom": "15px"}),
        dcc.RadioItems(
            id="analysis-mode",
            options=[
                {"label": " General Pollutant Analysis", "value": "general"},
                {"label": " Specialized Analysis", "value": "nox"}
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
                html.Label("Select Pollutant:", style={
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
                html.Label("Select Station:", style={
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
    
    # Specialized Analysis Controls
    html.Div(id="nox-controls", children=[
        html.Div([

            html.Div([
                html.Label("Select Pollutants:", style={
                    "fontWeight": "bold",
                    "marginBottom": "8px",
                    "display": "block",
                    "color": "#2c3e50"
                }),
                dcc.Dropdown(
                    id="specialized-pollutant-selector",
                    options=[{"label": pol, "value": pol} for pol in pollutants],
                    value=[],         # default list
                    multi=True,            # consente selezione multipla
                    clearable=False
                )
            ], style={"flex": "2", "marginRight": "15px"}),

            html.Div([
                html.Label("Select Province:", style={
                    "fontWeight": "bold",
                    "marginBottom": "8px",
                    "display": "block",
                    "color": "#2c3e50"
                }),
                dcc.Dropdown(
                    id="specialized-province-selector",
                    options=[{"label": "All", "value": "All"}] + [{"label": p, "value": p} for p in get_provinces()],
                    value="All",  # default value
                    clearable=False
                )
            ], style={"flex": "1", "marginRight": "15px"}),
            
            
            html.Div([
                html.Label("Data Smoothing:", style={
                    "fontWeight": "bold",
                    "marginBottom": "8px",
                    "display": "block",
                    "color": "#2c3e50"
                }),
                dcc.Dropdown(
                    id="specialized-smoothing",
                    options=get_smoothing_options(),
                    value="raw",
                    clearable=False
                )
            ], style={"flex": "1", "marginRight": "15px"}),

            html.Div([
                html.Label("Date Range:", style={
                    "fontWeight": "bold",
                    "marginBottom": "8px",
                    "display": "block",
                    "color": "#2c3e50"
                }),
                dcc.DatePickerRange(
                    id="nox-date-range",
                    min_date_allowed=datetime(2020, 1, 1),
                    max_date_allowed=datetime(2025, 12, 31),
                    start_date=datetime(2024, 12, 1),
                    end_date=datetime(2024, 12, 31),
                    display_format="DD/MM/YYYY",
                    style={"width": "100%"}
                )
            ], style={"flex": "1.5", "marginRight": "15px"}),

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
    [
        Output("trend-chart", "figure"),
        Output("summary-cards", "children"),
        Output("redirect-trend", "children")
    ],
    [
        Input("analysis-mode", "value"),
        Input("trend-pollutant-selector", "value"),
        Input("trend-station-selector", "value"),
        Input("specialized-province-selector", "value"),
        Input("specialized-pollutant-selector", "value"),
        Input("nox-date-range", "start_date"),
        Input("nox-date-range", "end_date"),
        Input("specialized-smoothing", "value"),
        Input("session", "data")
    ]
)
def update_chart_and_summary(mode, pollutant, station, province, nox_pollutant, start_date, end_date, smoothing, session_data):
    """
    Update the chart and summary based on the selected analysis mode and parameters.
    Handles user authentication, input validation, data fetching, and visualization.
    """
    # Convert start_date and end_date to datetime objects if provided
    if start_date:
        start_date = datetime.fromisoformat(start_date)
    if end_date:
        end_date = datetime.fromisoformat(end_date)

    # Check if user is logged in; if not, redirect to login page
    if not session_data or not session_data.get("logged_in"):
        fig = go.Figure()
        fig.add_annotation(
            text="Redirecting to login...",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            xanchor='center', yanchor='middle',
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(height=300)
        return fig, "", dcc.Location(href="/login", id="redirect-now")

    # === GENERAL ANALYSIS MODE ===
    if mode == "general":
        # Validate that both pollutant and station are selected
        if not pollutant or not station:
            empty_fig = go.Figure()
            empty_fig.add_annotation(
                text="Please select both pollutant and station",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                xanchor='center', yanchor='middle',
                showarrow=False,
                font=dict(size=16, color="gray")
            )
            empty_fig.update_layout(
                title="Select Filters",
                height=400,
                xaxis=dict(showgrid=False, showticklabels=False),
                yaxis=dict(showgrid=False, showticklabels=False)
            )
            empty_summary = html.Div(
                "Select pollutant and station to view summary",
                style={"textAlign": "center", "color": "gray", "padding": "20px"}
            )
            return empty_fig, empty_summary, no_update

        # Fetch sensor IDs for the selected pollutant and station
        id_sensore = get_idsensore(df_all, pollutant, station)
        # Fetch sensor data from API for these sensor IDs
        df_sensor = fetch_sensor_data_api(id_sensore)

        # Create time series chart and summary cards for the selected pollutant and station
        fig = create_trend_chart(df_sensor, pollutant, station)
        summary = create_summary_cards(df_sensor, pollutant)

    # === SPECIALIZED ANALYSIS MODE ===
    else:
        # Ensure nox_pollutant is a list
        if not isinstance(nox_pollutant, list):
            nox_pollutant = [nox_pollutant]

        # Handle 'All' province selection as None (no filter)
        if province == "All":
            province = None

        # Fetch data for multiple pollutants with date range filtering
        df_nox = fetch_data_multiple(nox_pollutant, province, start_date=start_date, end_date=end_date)
        
        # print(f"--> Fetching NOx data for {province}, {nox_pollutant}, smoothing: {smoothing} \n\n")

        # Handle case where no data is returned or expected column missing
        if df_nox.empty or "valore" not in df_nox.columns:
            fig = go.Figure()
            fig.add_annotation(
                text="No data available for the selected filters",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=16, color="gray")
            )
            fig.update_layout(height=300)
            summary = html.Div(
                "No data available for the selected filters",
                style={"textAlign": "center", "color": "gray", "padding": "20px"}
            )
            return fig, summary, no_update

        # Apply smoothing based on user selection
        if smoothing == "smoothed_7":
            df_nox["smoothed"] = df_nox.groupby("pollutant")["valore"].transform(lambda x: x.rolling(7, min_periods=1).mean())
        elif smoothing == "smoothed_14":
            df_nox["smoothed"] = df_nox.groupby("pollutant")["valore"].transform(lambda x: x.rolling(14, min_periods=2).mean())
        else:
            df_nox["smoothed"] = df_nox["valore"]

        # Create multi-pollutant NOx chart and summary cards
        fig = create_nox_chart_multi(df_nox, smoothing=smoothing, province=province)
        summary = create_summary_cards_per_pollutant(df_nox, nox_pollutant)

    return fig, summary, no_update

import dash
from dash import html, dcc, Output, Input, callback
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
from components.fetch_pollutant import fetch_pollutant

# Register the page
dash.register_page(__name__, path="/trend", name="Trends")

# Fetch initial data for dropdowns
df_all = fetch_pollutant()
pollutants = sorted(df_all["nometiposensore"].dropna().unique()) if not df_all.empty else []
stations = sorted(df_all["nomestazione"].dropna().unique()) if not df_all.empty else []

def fetch_sensor_data(pollutant=None, station=None):
    """
    Fetch sensor data from CSV or database
    This function should be adapted to your actual data source
    """
    try:
        # For now, using sample data - replace with your actual data fetch logic
        import pandas as pd
        import numpy as np
        from datetime import datetime, timedelta
        
        # Generate sample time series data for demonstration
        # Replace this with your actual sensor data fetching logic
        dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
        
        if pollutant and station:
            # Simulate realistic air quality data
            if 'PM' in pollutant:
                base_value = 25
                noise_level = 15
            elif 'NO' in pollutant:
                base_value = 35
                noise_level = 20
            elif 'O3' in pollutant:
                base_value = 45
                noise_level = 25
            else:
                base_value = 30
                noise_level = 10
                
            # Add seasonal variation and random noise
            seasonal = 10 * np.sin(2 * np.pi * np.arange(len(dates)) / 365.25)
            noise = np.random.normal(0, noise_level, len(dates))
            values = base_value + seasonal + noise
            values = np.maximum(values, 0)  # Ensure non-negative values
            
            df = pd.DataFrame({
                'data': dates,
                'valore': values,
                'nomestazione': station,
                'nometiposensore': pollutant,
                'stato': 'V'  # Valid status
            })
            
            return df
        else:
            return pd.DataFrame()
            
    except Exception as e:
        print(f"Error fetching sensor data: {e}")
        return pd.DataFrame()

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

    # Create the time series plot
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
    
    # Customize the layout
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
    
    # Update line style
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
    # Page Header
    html.Div([
        html.H1("📈 Air Quality Trends", style={
            "textAlign": "center",
            "color": "rgb(19, 129, 159)",
            "marginBottom": "10px",
            "fontSize": "32px"
        }),
        html.P("Analyze temporal patterns in air quality measurements", style={
            "textAlign": "center",
            "color": "#7f8c8d",
            "fontSize": "16px",
            "marginBottom": "30px"
        })
    ]),
    
    # Control Panel
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
    ], style={
        "display": "flex",
        "backgroundColor": "white",
        "padding": "20px",
        "borderRadius": "10px",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
        "margin": "0 20px 20px 20px"
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
        html.P("💡 Tip: Use the zoom and pan tools to explore specific time periods in detail.", style={
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

# Callback to update station options based on selected pollutant
@callback(
    Output("trend-station-selector", "options"),
    Input("trend-pollutant-selector", "value")
)
def update_station_options(selected_pollutant):
    """Update available stations based on selected pollutant"""
    if not selected_pollutant:
        return []
    
    # Filter stations that have the selected pollutant
    df_filtered = df_all[df_all["nometiposensore"] == selected_pollutant]
    available_stations = sorted(df_filtered["nomestazione"].dropna().unique())
    
    return [{"label": station, "value": station} for station in available_stations]

# Main callback to update chart and summary
@callback(
    [Output("trend-chart", "figure"),
     Output("summary-cards", "children")],
    [Input("trend-pollutant-selector", "value"),
     Input("trend-station-selector", "value")]
)
def update_trend_chart(selected_pollutant, selected_station):
    """Update the trend chart based on selected pollutant and station"""
    if not selected_pollutant or not selected_station:
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
        return empty_fig, empty_summary
    
    # Fetch sensor data for the selected combination
    df_sensor = fetch_sensor_data(selected_pollutant, selected_station)
    
    # Create chart and summary
    fig = create_trend_chart(df_sensor, selected_pollutant, selected_station)
    summary = create_summary_cards(df_sensor, selected_pollutant)
    
    return fig, summary
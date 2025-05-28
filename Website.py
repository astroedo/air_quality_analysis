# Enhanced Lombardia Air Quality Monitoring Dashboard
import dash
from dash import dcc, html, Input, Output, dash_table
import dash_leaflet as dl
import pandas as pd
import psycopg2
from sqlalchemy import create_engine
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database Configuration
DB_CONFIG = {
    "dbname": "lombardia_air_quality",
    "user": "airdata_user", 
    "password": "user",
    "host": "localhost",
    "port": "5432"
}

# Pollutant Grouping Configuration
POLLUTANT_GROUPS = {
    "NOx Compounds": ["Ossidi di Azoto", "Biossido di Azoto", "Monossido di Azoto"],
    "Particulate Matter": ["PM10", "PM10 (SM2005)", "Particelle sospese PM2.5", "Particolato Totale Sospeso"],
    "Heavy Metals": ["Arsenico", "Nikel", "Piombo", "Cadmio"],
    "Aromatic Compounds": ["Benzene", "Benzo(a)pirene"],
    "Gaseous Pollutants": ["Ozono", "Monossido di Carbonio", "Biossido di Zolfo", "Ammoniaca"],
    "Other Indicators": ["BlackCarbon"]
}

# Color scheme for groups
GROUP_COLORS = {
    "NOx Compounds": "#e74c3c",
    "Particulate Matter": "#f39c12",
    "Heavy Metals": "#8e44ad",
    "Aromatic Compounds": "#2ecc71",
    "Gaseous Pollutants": "#3498db",
    "Other Indicators": "#34495e"
}

def get_pollutant_group(pollutant):
    """Get the group for a given pollutant"""
    for group, pollutants in POLLUTANT_GROUPS.items():
        if pollutant in pollutants:
            return group
    return "Other"

def fetch_station_data():
    """Fetch station data from PostgreSQL database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        query = """
        SELECT idsensore, nomestazione, lat, lng, nometiposensore, provincia, comune, quota
        FROM station
        WHERE lat IS NOT NULL AND lng IS NOT NULL;
        """
        df = pd.read_sql(query, conn)
        conn.close()
        logger.info(f"Fetched {len(df)} station records")
        return df
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        # Return sample data based on uploaded CSV
        return pd.read_csv('station.csv')

def fetch_sensor_data():
    """Fetch sensor measurement data"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        query = """
        SELECT s.idsensore, s.data, s.valore, s.stato, st.nometiposensore, st.nomestazione
        FROM sensors s
        JOIN station st ON s.idsensore = st.idsensore
        WHERE s.data >= CURRENT_DATE - INTERVAL '30 days'
        ORDER BY s.data DESC;
        """
        df = pd.read_sql(query, conn)
        conn.close()
        logger.info(f"Fetched {len(df)} sensor readings")
        return df
    except Exception as e:
        logger.error(f"Sensor data fetch failed: {e}")
        # Return sample data
        return pd.read_csv('sensors.csv')

def calculate_data_quality(sensor_df):
    """Calculate data quality metrics"""
    total_readings = len(sensor_df)
    valid_readings = len(sensor_df[sensor_df['stato'] == 'VA'])
    invalid_readings = total_readings - valid_readings
    
    valid_percentage = (valid_readings / total_readings * 100) if total_readings > 0 else 0
    invalid_percentage = (invalid_readings / total_readings * 100) if total_readings > 0 else 0
    
    return {
        'total': total_readings,
        'valid': valid_readings,
        'invalid': invalid_readings,
        'valid_percentage': valid_percentage,
        'invalid_percentage': invalid_percentage
    }

def create_layer_group(df, group_name, pollutants):
    """Create a layer group with markers for pollutants in a specific group"""
    if df.empty:
        return dl.LayerGroup([], id=f"layer-{group_name}")
    
    df_filtered = df[df["nometiposensore"].isin(pollutants)]
    markers = []
    color = GROUP_COLORS.get(group_name, "#95a5a6")
    
    for _, row in df_filtered.iterrows():
        marker = dl.CircleMarker(
            center=[row["lat"], row["lng"]],
            radius=8,
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.7,
            weight=2,
            children=dl.Popup([
                html.Div([
                    html.H4(row['nomestazione'], style={'margin': '0 0 10px 0', 'color': '#2c3e50'}),
                    html.P([
                        html.Strong("Pollutant: "), 
                        html.Span(row['nometiposensore'])
                    ], style={'margin': '5px 0'}),
                    html.P([
                        html.Strong("Group: "), 
                        html.Span(group_name)
                    ], style={'margin': '5px 0'}),
                    html.P([
                        html.Strong("Location: "), 
                        html.Span(f"{row['comune']}, {row['provincia']}")
                    ], style={'margin': '5px 0'}),
                    html.P([
                        html.Strong("Altitude: "), 
                        html.Span(f"{row['quota']}m")
                    ], style={'margin': '5px 0'}),
                    html.P([
                        html.Strong("Coordinates: "), 
                        html.Span(f"{row['lat']:.4f}, {row['lng']:.4f}")
                    ], style={'margin': '5px 0'})
                ], style={'fontFamily': 'Arial, sans-serif'})
            ])
        )
        markers.append(marker)
    
    return dl.LayerGroup(markers, id=f"layer-{group_name}")

# Initialize Dash app
app = dash.Dash(__name__)
app.title = "Lombardia Air Quality Monitor - Enhanced"

# Load initial data
try:
    df_stations = fetch_station_data()
    df_sensors = fetch_sensor_data()
    
    # Get available groups based on actual data
    available_pollutants = df_stations['nometiposensore'].unique()
    available_groups = {}
    for group, pollutants in POLLUTANT_GROUPS.items():
        group_pollutants = [p for p in pollutants if p in available_pollutants]
        if group_pollutants:
            available_groups[group] = group_pollutants
    
    # Calculate data quality
    data_quality = calculate_data_quality(df_sensors)
    
except Exception as e:
    logger.error(f"Initial data load failed: {e}")
    df_stations = pd.DataFrame()
    df_sensors = pd.DataFrame()
    available_groups = {}
    data_quality = {'valid_percentage': 0, 'invalid_percentage': 100, 'total': 0}

# Enhanced Layout
app.layout = html.Div([
    # Header Section
    html.Div([
        html.Div([
            html.H1("🌍 Air Quality Monitoring Dashboard", 
                    style={
                        "margin": "0",
                        "fontFamily": "Arial, sans-serif",
                        "fontWeight": "bold",
                        "color": "#2c3e50",
                        "fontSize": "2.5rem"
                    }),
            html.P("Real-time monitoring of air quality stations across Lombardia region",
                   style={
                       "margin": "10px 0 0 0",
                       "fontFamily": "Arial, sans-serif",
                       "color": "#7f8c8d",
                       "fontSize": "1.1rem"
                   })
        ], style={"textAlign": "center", "padding": "30px 20px"})
    ], style={
        "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        "color": "white",
        "marginBottom": "20px"
    }),
    
    # Data Quality Indicator Bar
    html.Div([
        html.Div([
            html.H3("📊 Data Quality Overview", 
                   style={"margin": "0 0 15px 0", "color": "#2c3e50", "fontSize": "1.3rem"}),
            html.Div([
                # Valid Data
                html.Div([
                    html.Div(style={
                        "width": f"{data_quality['valid_percentage']}%",
                        "height": "30px",
                        "backgroundColor": "#27ae60",
                        "borderRadius": "15px 0 0 15px" if data_quality['valid_percentage'] < 100 else "15px",
                        "display": "flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "color": "white",
                        "fontWeight": "bold",
                        "fontSize": "14px"
                    }, children=f"Valid: {data_quality['valid_percentage']:.1f}%"),
                ], style={"flex": f"{data_quality['valid_percentage']}", "minWidth": "80px"}),
                
                # Invalid Data
                html.Div([
                    html.Div(style={
                        "width": "100%",
                        "height": "30px",
                        "backgroundColor": "#e74c3c",
                        "borderRadius": "0 15px 15px 0" if data_quality['invalid_percentage'] < 100 else "15px",
                        "display": "flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "color": "white",
                        "fontWeight": "bold",
                        "fontSize": "14px"
                    }, children=f"Invalid: {data_quality['invalid_percentage']:.1f}%"),
                ], style={"flex": f"{data_quality['invalid_percentage']}", "minWidth": "80px"})
            ], style={
                "display": "flex",
                "backgroundColor": "#ecf0f1",
                "borderRadius": "15px",
                "overflow": "hidden",
                "border": "2px solid #bdc3c7"
            }),
            
            html.P(f"Total readings analyzed: {data_quality['total']:,}", 
                  style={"margin": "10px 0 0 0", "color": "#7f8c8d", "fontSize": "14px"})
        ], style={
            "backgroundColor": "white",
            "padding": "20px",
            "borderRadius": "10px",
            "boxShadow": "0 4px 6px rgba(0,0,0,0.1)",
            "margin": "0 20px 20px 20px"
        })
    ]),
    
    # Map Section
    html.Div([
        # Main map
        dl.Map(
            id="map",
            center=[45.5, 9.2],
            zoom=8,
            children=[
                dl.TileLayer(
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                )
            ],
            style={
                "width": "100%", 
                "height": "70vh", 
                "borderRadius": "10px",
                "border": "2px solid #bdc3c7"
            }
        ),
        
        # Enhanced Control Panel
        html.Div([
            html.H4("🎛️ Controls", style={"margin": "0 0 15px 0", "color": "#2c3e50"}),
            
            html.Label("Select Pollutant Group:", 
                      style={"fontWeight": "bold", "marginBottom": "8px", "display": "block"}),
            dcc.Dropdown(
                id="group-selector",
                options=[{"label": f"{group} ({len(pollutants)})", "value": group} 
                        for group, pollutants in available_groups.items()],
                value=list(available_groups.keys())[0] if available_groups else None,
                clearable=False,
                placeholder="Select a pollutant group...",
                style={"marginBottom": "15px"}
            ),
            
            html.Div(id="group-info", style={"fontSize": "14px", "marginBottom": "15px"}),
            
            html.Hr(style={"margin": "15px 0"}),
            
            # Legend
            html.H5("🏷️ Legend", style={"margin": "0 0 10px 0", "color": "#2c3e50"}),
            html.Div([
                html.Div([
                    html.Div(style={
                        "width": "20px",
                        "height": "20px",
                        "backgroundColor": color,
                        "borderRadius": "50%",
                        "display": "inline-block",
                        "marginRight": "10px",
                        "border": "2px solid white",
                        "boxShadow": "0 2px 4px rgba(0,0,0,0.2)"
                    }),
                    html.Span(group, style={"fontSize": "12px", "verticalAlign": "top"})
                ], style={"marginBottom": "8px"})
                for group, color in GROUP_COLORS.items() if group in available_groups
            ]),
            
            html.Hr(style={"margin": "15px 0"}),
            html.Div(id="station-count", style={"fontSize": "14px", "color": "#7f8c8d"})
            
        ], style={
            "position": "absolute",
            "top": "20px",
            "right": "20px",
            "zIndex": "1000",
            "width": "320px",
            "backgroundColor": "rgba(255, 255, 255, 0.95)",
            "padding": "25px",
            "border": "1px solid #bdc3c7",
            "borderRadius": "10px",
            "boxShadow": "0 8px 16px rgba(0,0,0,0.15)",
            "fontFamily": "Arial, sans-serif",
            "backdropFilter": "blur(10px)",
            "maxHeight": "80vh",
            "overflowY": "auto"
        })
    ], style={"position": "relative", "margin": "20px", "marginBottom": "40px"}),
    
    # Analytics Section
    html.Div([
        html.H2("📈 Analytics Dashboard", 
               style={"textAlign": "center", "margin": "40px 0 30px 0", "color": "#2c3e50"}),
        
        # Graphs Container
        html.Div([
            # Left Graph - Time Series
            html.Div([
                dcc.Graph(id="timeseries-chart")
            ], style={"width": "50%", "padding": "0 10px"}),
            
            # Right Graph - Distribution
            html.Div([
                dcc.Graph(id="distribution-chart")
            ], style={"width": "50%", "padding": "0 10px"})
        ], style={"display": "flex", "margin": "20px 0"}),
        
        # Bottom Graph - Province Summary
        html.Div([
            dcc.Graph(id="province-chart")
        ], style={"margin": "20px 10px"})
    ], style={"margin": "20px"}),
    
    # Footer
    html.Div([
        html.P("Data source: Lombardia Environmental Agency | Dashboard by Air Quality Monitoring System",
               style={
                   "textAlign": "center",
                   "fontSize": "12px",
                   "color": "#95a5a6",
                   "margin": "40px 20px 20px 20px",
                   "fontFamily": "Arial, sans-serif"
               })
    ])
])

# Callbacks
@app.callback(
    [Output("map", "children"),
     Output("station-count", "children"),
     Output("group-info", "children")],
    [Input("group-selector", "value")]
)
def update_map_layers(selected_group):
    """Update map layers based on selected pollutant group"""
    try:
        # Fetch fresh data
        df_live = fetch_station_data()
        
        # Base tile layer
        base_layer = dl.TileLayer(
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        )
        
        layers = [base_layer]
        station_info = "No group selected"
        group_info = ""
        
        if selected_group and selected_group in available_groups:
            # Add group layer
            group_pollutants = available_groups[selected_group]
            group_layer = create_layer_group(df_live, selected_group, group_pollutants)
            layers.append(group_layer)
            
            # Count stations for this group
            station_count = len(df_live[df_live["nometiposensore"].isin(group_pollutants)])
            station_info = f"📍 {station_count} stations monitoring {selected_group}"
            
            # Group info
            group_info = html.Div([
                html.P(f"Pollutants in this group:", style={"fontWeight": "bold", "margin": "0 0 5px 0"}),
                html.Ul([
                    html.Li(pollutant, style={"fontSize": "12px", "margin": "2px 0"}) 
                    for pollutant in group_pollutants
                ], style={"margin": "0", "paddingLeft": "20px"})
            ])
        
        return layers, station_info, group_info
        
    except Exception as e:
        logger.error(f"Error updating map: {e}")
        base_layer = dl.TileLayer(
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        )
        return [base_layer], "⚠️ Error loading data", ""

@app.callback(
    [Output("timeseries-chart", "figure"),
     Output("distribution-chart", "figure"),
     Output("province-chart", "figure")],
    [Input("group-selector", "value")]
)
def update_charts(selected_group):
    """Update all charts based on selected group"""
    try:
        # Fetch sensor data
        df_sensors_live = fetch_sensor_data()
        df_stations_live = fetch_station_data()
        
        if df_sensors_live.empty or selected_group not in available_groups:
            # Return empty charts
            empty_fig = go.Figure()
            empty_fig.add_annotation(text="No data available", xref="paper", yref="paper",
                                   x=0.5, y=0.5, showarrow=False, font_size=16)
            return empty_fig, empty_fig, empty_fig
        
        # Filter data for selected group
        group_pollutants = available_groups[selected_group]
        
        # Merge sensor data with station data
        df_merged = df_sensors_live.merge(
            df_stations_live[['idsensore', 'nometiposensore', 'provincia']], 
            on='idsensore', 
            how='left'
        )
        df_filtered = df_merged[df_merged['nometiposensore'].isin(group_pollutants)]
        
        # Time Series Chart
        if not df_filtered.empty and 'data' in df_filtered.columns:
            df_filtered['data'] = pd.to_datetime(df_filtered['data'])
            daily_avg = df_filtered.groupby(['data', 'nometiposensore'])['valore'].mean().reset_index()
            
            timeseries_fig = px.line(
                daily_avg, 
                x='data', 
                y='valore', 
                color='nometiposensore',
                title=f"Time Series - {selected_group}",
                labels={'data': 'Date', 'valore': 'Concentration', 'nometiposensore': 'Pollutant'}
            )
            timeseries_fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font={'family': 'Arial'},
                title_x=0.5
            )
        else:
            timeseries_fig = go.Figure()
            timeseries_fig.add_annotation(text="No time series data", xref="paper", yref="paper",
                                        x=0.5, y=0.5, showarrow=False)
        
        # Distribution Chart
        if not df_filtered.empty:
            distribution_fig = px.box(
                df_filtered,
                x='nometiposensore',
                y='valore',
                title=f"Value Distribution - {selected_group}",
                labels={'nometiposensore': 'Pollutant', 'valore': 'Concentration'}
            )
            distribution_fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font={'family': 'Arial'},
                title_x=0.5,
                xaxis_tickangle=-45
            )
        else:
            distribution_fig = go.Figure()
            distribution_fig.add_annotation(text="No distribution data", xref="paper", yref="paper",
                                          x=0.5, y=0.5, showarrow=False)
        
        # Province Chart
        if not df_filtered.empty and 'provincia' in df_filtered.columns:
            province_summary = df_filtered.groupby('provincia').agg({
                'valore': 'mean',
                'idsensore': 'count'
            }).reset_index()
            province_summary.columns = ['provincia', 'avg_concentration', 'station_count']
            
            province_fig = px.bar(
                province_summary,
                x='provincia',
                y='avg_concentration',
                title=f"Average Concentration by Province - {selected_group}",
                labels={'provincia': 'Province', 'avg_concentration': 'Average Concentration'},
                color='avg_concentration',
                color_continuous_scale='Viridis'
            )
            province_fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font={'family': 'Arial'},
                title_x=0.5
            )
        else:
            province_fig = go.Figure()
            province_fig.add_annotation(text="No province data", xref="paper", yref="paper",
                                      x=0.5, y=0.5, showarrow=False)
        
        return timeseries_fig, distribution_fig, province_fig
        
    except Exception as e:
        logger.error(f"Error updating charts: {e}")
        empty_fig = go.Figure()
        empty_fig.add_annotation(text="Error loading chart data", xref="paper", yref="paper",
                               x=0.5, y=0.5, showarrow=False)
        return empty_fig, empty_fig, empty_fig

# Run the app
if __name__ == "__main__":
    print("🚀 Starting Enhanced Lombardia Air Quality Dashboard...")
    print("🌟 Features: Grouped pollutants, data quality metrics, interactive analytics")
    print("📱 Open your browser to: http://127.0.0.1:8050")
    print("🔄 Press Ctrl+C to stop the server")
    
    app.run(
        debug=True,
        host='127.0.0.1',
        port=8050,
        dev_tools_ui=True,
        dev_tools_props_check=True
    )
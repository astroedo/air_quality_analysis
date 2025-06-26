# pages/home_page.py
"""
Enhanced home page with sensor map, histogram display, and team section.
"""

import dash
from dash import html, dcc, Input, Output, callback
import dash_leaflet as dl
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import requests
from components.fetch_pollutant import fetch_pollutant
import psycopg2

dash.register_page(__name__, path="/", name="Home")

# Database connection function
def connect_to_postgres():
    return psycopg2.connect(
        host="localhost",
        database="lombardia_air_quality",
        user="airdata_user",
        password="user"
    )

# Fetch measurement data for histogram
def fetch_measurement_data(pollutant_group=None, province=None, start_date=None, end_date=None):
    """Fetch measurement data based on filters"""
    try:
        conn = connect_to_postgres()
        
        # Base query
        query = """
        SELECT m.valore, s.nometiposensore, s.provincia, s.nomestazione, m.data
        FROM measurement m
        JOIN station s ON m.idsensore = s.idsensore
        WHERE m.valore IS NOT NULL AND s.lat IS NOT NULL AND s.lng IS NOT NULL
        """
        
        params = []
        
        # Add filters
        if pollutant_group and pollutant_group != "All":
            if pollutant_group == "PM":
                query += " AND (s.nometiposensore LIKE 'PM%')"
            elif pollutant_group == "NOx":
                query += " AND (s.nometiposensore IN ('NO', 'NO2', 'NOx'))"
            elif pollutant_group == "Ozone":
                query += " AND s.nometiposensore = 'O3'"
            else:
                query += " AND s.nometiposensore = %s"
                params.append(pollutant_group)
        
        if province and province != "All":
            query += " AND s.provincia = %s"
            params.append(province)
            
        if start_date:
            query += " AND m.data >= %s"
            params.append(start_date)
            
        if end_date:
            query += " AND m.data <= %s"
            params.append(end_date)
            
        query += " ORDER BY m.data DESC LIMIT 10000"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
        
    except Exception as e:
        print(f"Error fetching measurement data: {e}")
        return pd.DataFrame()

# Get available provinces
def get_provinces():
    """Get list of available provinces"""
    try:
        conn = connect_to_postgres()
        df = pd.read_sql("SELECT DISTINCT provincia FROM station WHERE provincia IS NOT NULL ORDER BY provincia", conn)
        conn.close()
        return df['provincia'].tolist()
    except:
        return []

# Create map with filtered stations
def create_filtered_map(pollutant_group=None, province=None):
    """Create map with filtered stations"""
    try:
        # Fetch station data
        df_stations = fetch_pollutant()
        
        if df_stations.empty:
            return dl.Map(
                center=[45.5, 9.2],
                zoom=8,
                children=[
                    dl.TileLayer(url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"),
                ],
                style={"width": "100%", "height": "400px"}
            )
        
        # Apply filters
        if pollutant_group and pollutant_group != "All":
            if pollutant_group == "PM":
                df_stations = df_stations[df_stations["nometiposensore"].str.contains("PM", na=False)]
            elif pollutant_group == "NOx":
                df_stations = df_stations[df_stations["nometiposensore"].isin(["NO", "NO2", "NOx"])]
            elif pollutant_group == "Ozone":
                df_stations = df_stations[df_stations["nometiposensore"] == "O3"]
            else:
                df_stations = df_stations[df_stations["nometiposensore"] == pollutant_group]
        
        if province and province != "All":
            df_stations = df_stations[df_stations["provincia"] == province]
        
        # Group stations by location
        grouped = df_stations.groupby(["nomestazione", "lat", "lng"]).agg({
            "nometiposensore": list,
            "provincia": "first"
        }).reset_index()
        
        # Create markers
        markers = []
        for _, row in grouped.iterrows():
            if pd.notna(row["lat"]) and pd.notna(row["lng"]):
                popup_content = [
                    html.H4(row["nomestazione"], style={"margin": "5px 0"}),
                    html.P(f"Province: {row['provincia']}", style={"margin": "2px 0"}),
                    html.P(f"Coordinates: {row['lat']:.4f}, {row['lng']:.4f}", style={"margin": "2px 0"}),
                    html.P("Pollutants:", style={"margin": "5px 0 2px 0", "fontWeight": "bold"}),
                    html.Ul([html.Li(p) for p in row["nometiposensore"]], style={"margin": "0", "paddingLeft": "20px"})
                ]
                
                marker = dl.Marker(
                    position=[row["lat"], row["lng"]],
                    children=dl.Popup(popup_content)
                )
                markers.append(marker)
        
        return dl.Map(
            center=[45.5, 9.2],
            zoom=8,
            children=[
                dl.TileLayer(url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"),
                dl.LayerGroup(markers)
            ],
            style={"width": "100%", "height": "400px", "borderRadius": "8px"}
        )
        
    except Exception as e:
        print(f"Error creating map: {e}")
        return dl.Map(
            center=[45.5, 9.2],
            zoom=8,
            children=[dl.TileLayer(url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png")],
            style={"width": "100%", "height": "400px"}
        )

# Main layout
layout = html.Div([
    # Hero Section
    html.Div([
        html.Div([
            html.Img(
                src="/assets/logo.png", 
                style={
                    "height": "80px", 
                    "width": "80px", 
                    "marginBottom": "20px"
                }
            ),
            html.H1(
                "Welcome to GeoAir", 
                style={
                    "fontSize": "3.5rem", 
                    "marginBottom": "20px",
                    "color": "white",
                    "textShadow": "2px 2px 4px rgba(0,0,0,0.5)",
                    "margin": "0 auto 20px auto",
                    "width": "fit-content"
                }
            ),
            html.P(
                "Monitor air quality across Lombardia with real-time data and advanced analytics", 
                style={
                    "fontSize": "1.3rem",
                    "color": "white",
                    "textShadow": "1px 1px 2px rgba(0,0,0,0.5)",
                    "maxWidth": "600px",
                    "margin": "0 auto 30px auto",
                    "lineHeight": "1.5"
                }
            ),
            html.Div([
                dcc.Link(
                    "Explore Map →",
                    href="/map",
                    style={
                        "padding": "12px 30px",
                        "fontSize": "1.2rem",
                        "color": "white",
                        "backgroundColor": "rgba(255,255,255,0.2)",
                        "textDecoration": "none",
                        "borderRadius": "25px",
                        "border": "2px solid white",
                        "marginRight": "15px",
                        "display": "inline-block",
                        "transition": "all 0.3s ease"
                    }
                ),
                dcc.Link(
                    "View Trends →",
                    href="/trend",
                    style={
                        "padding": "12px 30px",
                        "fontSize": "1.2rem",
                        "color": "rgb(19, 129, 159)",
                        "backgroundColor": "white",
                        "textDecoration": "none",
                        "borderRadius": "25px",
                        "display": "inline-block",
                        "transition": "all 0.3s ease"
                    }
                )
            ], style={
                "display": "flex",
                "justifyContent": "center",
                "alignItems": "center",
                "gap": "15px",
                "marginTop": "30px"
            })
        ], style={
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "center",
            "alignItems": "center",
            "padding": "100px 20px",
            "maxWidth": "800px",
            "margin": "0 auto"
        })
    ], style={
        "backgroundImage": "url('https://images.unsplash.com/photo-1506744038136-46273834b3fb')",
        "backgroundSize": "cover",
        "backgroundPosition": "center",
        "color": "white",
        "minHeight": "70vh",
        "display": "flex",
        "alignItems": "center"
    }),
    
    # Interactive Dashboard Section
    html.Div([
        html.H2(
            "🗺️ Interactive Air Quality Dashboard", 
            style={
                "textAlign": "center", 
                "color": "rgb(19, 129, 159)",
                "marginBottom": "40px",
                "fontSize": "2.5rem"
            }
        ),
        
        # Filters Section
        html.Div([
            html.Div([
                html.Label("📅 Date Range:", style={"fontWeight": "bold", "marginBottom": "8px", "display": "block"}),
                dcc.DatePickerRange(
                    id="date-range-picker",
                    start_date=date(2024, 1, 1),
                    end_date=date(2024, 12, 31),
                    display_format="YYYY-MM-DD",
                    style={"width": "100%"}
                )
            ], style={"flex": "1", "marginRight": "20px"}),
            
            html.Div([
                html.Label("🏭 Pollutant Group:", style={"fontWeight": "bold", "marginBottom": "8px", "display": "block"}),
                dcc.Dropdown(
                    id="pollutant-group-dropdown",
                    options=[
                        {"label": "All Pollutants", "value": "All"},
                        {"label": "Particulate Matter (PM)", "value": "PM"},
                        {"label": "Nitrogen Oxides (NOx)", "value": "NOx"},
                        {"label": "Ozone (O3)", "value": "Ozone"}
                    ],
                    value="All",
                    clearable=False
                )
            ], style={"flex": "1", "marginRight": "20px"}),
            
            html.Div([
                html.Label("🏛️ Province:", style={"fontWeight": "bold", "marginBottom": "8px", "display": "block"}),
                dcc.Dropdown(
                    id="province-dropdown",
                    options=[{"label": "All Provinces", "value": "All"}] + 
                            [{"label": p, "value": p} for p in get_provinces()],
                    value="All",
                    clearable=False
                )
            ], style={"flex": "1"})
        ], style={
            "display": "flex",
            "backgroundColor": "white",
            "padding": "25px",
            "borderRadius": "10px",
            "boxShadow": "0 4px 12px rgba(0,0,0,0.1)",
            "marginBottom": "30px"
        }),
        
        # Map and Histogram Row
        html.Div([
            # Map Column
            html.Div([
                html.H3("📍 Station Locations", style={"color": "rgb(19, 129, 159)", "marginBottom": "15px"}),
                html.Div(id="sensor-map"),
                html.Div(id="station-info", style={"marginTop": "10px", "color": "#666", "fontSize": "14px"})
            ], style={
                "flex": "1",
                "marginRight": "20px",
                "backgroundColor": "white",
                "padding": "20px",
                "borderRadius": "10px",
                "boxShadow": "0 4px 12px rgba(0,0,0,0.1)"
            }),
            
            # Histogram Column
            html.Div([
                html.H3("📊 Sensor Distribution", style={"color": "rgb(19, 129, 159)", "marginBottom": "15px"}),
                dcc.Graph(id="sensor-histogram", style={"height": "400px"})
            ], style={
                "flex": "1",
                "backgroundColor": "white",
                "padding": "20px",
                "borderRadius": "10px",
                "boxShadow": "0 4px 12px rgba(0,0,0,0.1)"
            })
        ], style={"display": "flex", "marginBottom": "40px"})
    ], style={
        "maxWidth": "1400px",
        "margin": "0 auto",
        "padding": "60px 20px"
    }),
    
    # Team Section
    html.Div([
        html.H2(
            "👥 Meet Our Team", 
            style={
                "textAlign": "center", 
                "color": "white",
                "marginBottom": "50px",
                "fontSize": "2.5rem"
            }
        ),
        html.Div([
            # Team Member 1
            html.Div([
                html.Div([
                    html.H3("Alice Johnson", style={"color": "white", "marginBottom": "10px"}),
                    html.P("Data Scientist", style={"color": "rgba(255,255,255,0.8)", "fontSize": "1.1rem", "marginBottom": "15px"}),
                    html.P(
                        "Specialized in environmental data analysis and machine learning for air quality prediction.",
                        style={"color": "rgba(255,255,255,0.9)", "lineHeight": "1.5"}
                    )
                ], style={
                    "backgroundColor": "rgba(255,255,255,0.1)",
                    "padding": "30px",
                    "borderRadius": "15px",
                    "textAlign": "center",
                    "height": "200px",
                    "display": "flex",
                    "flexDirection": "column",
                    "justifyContent": "center"
                })
            ], style={"flex": "1", "margin": "0 15px"}),
            
            # Team Member 2
            html.Div([
                html.Div([
                    html.H3("Marco Rodriguez", style={"color": "white", "marginBottom": "10px"}),
                    html.P("Full-Stack Developer", style={"color": "rgba(255,255,255,0.8)", "fontSize": "1.1rem", "marginBottom": "15px"}),
                    html.P(
                        "Expert in web development and database design, creating scalable solutions for environmental monitoring.",
                        style={"color": "rgba(255,255,255,0.9)", "lineHeight": "1.5"}
                    )
                ], style={
                    "backgroundColor": "rgba(255,255,255,0.1)",
                    "padding": "30px",
                    "borderRadius": "15px",
                    "textAlign": "center",
                    "height": "200px",
                    "display": "flex",
                    "flexDirection": "column",
                    "justifyContent": "center"
                })
            ], style={"flex": "1", "margin": "0 15px"}),
            
            # Team Member 3
            html.Div([
                html.Div([
                    html.H3("Sarah Chen", style={"color": "white", "marginBottom": "10px"}),
                    html.P("Environmental Engineer", style={"color": "rgba(255,255,255,0.8)", "fontSize": "1.1rem", "marginBottom": "15px"}),
                    html.P(
                        "Environmental engineering background with focus on air quality monitoring and pollution control systems.",
                        style={"color": "rgba(255,255,255,0.9)", "lineHeight": "1.5"}
                    )
                ], style={
                    "backgroundColor": "rgba(255,255,255,0.1)",
                    "padding": "30px",
                    "borderRadius": "15px",
                    "textAlign": "center",
                    "height": "200px",
                    "display": "flex",
                    "flexDirection": "column",
                    "justifyContent": "center"
                })
            ], style={"flex": "1", "margin": "0 15px"}),
            
            # Team Member 4
            html.Div([
                html.Div([
                    html.H3("David Thompson", style={"color": "white", "marginBottom": "10px"}),
                    html.P("GIS Specialist", style={"color": "rgba(255,255,255,0.8)", "fontSize": "1.1rem", "marginBottom": "15px"}),
                    html.P(
                        "Geographic Information Systems expert specializing in spatial analysis and interactive mapping solutions.",
                        style={"color": "rgba(255,255,255,0.9)", "lineHeight": "1.5"}
                    )
                ], style={
                    "backgroundColor": "rgba(255,255,255,0.1)",
                    "padding": "30px",
                    "borderRadius": "15px",
                    "textAlign": "center",
                    "height": "200px",
                    "display": "flex",
                    "flexDirection": "column",
                    "justifyContent": "center"
                })
            ], style={"flex": "1", "margin": "0 15px"})
        ], style={
            "display": "flex",
            "maxWidth": "1200px",
            "margin": "0 auto"
        })
    ], style={
        "backgroundColor": "rgb(19, 129, 159)",
        "padding": "80px 20px",
        "marginTop": "40px"
    }),
    
    # Footer
    html.Div([
        html.P(
            "© 2025 GeoAir Team | Data source: Lombardia Environmental Agency", 
            style={
                "textAlign": "center",
                "color": "#95a5a6",
                "margin": "0",
                "fontSize": "14px"
            }
        )
    ], style={
        "backgroundColor": "#2c3e50",
        "padding": "20px"
    })
])

# Callbacks
@callback(
    [Output("sensor-map", "children"),
     Output("station-info", "children"),
     Output("sensor-histogram", "figure")],
    [Input("pollutant-group-dropdown", "value"),
     Input("province-dropdown", "value"),
     Input("date-range-picker", "start_date"),
     Input("date-range-picker", "end_date")]
)
def update_dashboard(pollutant_group, province, start_date, end_date):
    # Update map
    sensor_map = create_filtered_map(pollutant_group, province)
    
    # Get station count info
    try:
        df_stations = fetch_pollutant()
        if not df_stations.empty:
            # Apply filters for counting
            filtered_stations = df_stations.copy()
            
            if pollutant_group and pollutant_group != "All":
                if pollutant_group == "PM":
                    filtered_stations = filtered_stations[filtered_stations["nometiposensore"].str.contains("PM", na=False)]
                elif pollutant_group == "NOx":
                    filtered_stations = filtered_stations[filtered_stations["nometiposensore"].isin(["NO", "NO2", "NOx"])]
                elif pollutant_group == "Ozone":
                    filtered_stations = filtered_stations[filtered_stations["nometiposensore"] == "O3"]
            
            if province and province != "All":
                filtered_stations = filtered_stations[filtered_stations["provincia"] == province]
            
            num_stations = filtered_stations["nomestazione"].nunique()
            num_sensors = len(filtered_stations)
            station_info = f"📍 {num_stations} stations with {num_sensors} sensors"
        else:
            station_info = "No station data available"
    except:
        station_info = "Error loading station information"
    
    # Update sensor distribution chart
    try:
        df_stations = fetch_pollutant()
        if not df_stations.empty:
            # Apply filters for sensor distribution
            filtered_stations = df_stations.copy()
            
            if pollutant_group and pollutant_group != "All":
                if pollutant_group == "PM":
                    filtered_stations = filtered_stations[filtered_stations["nometiposensore"].str.contains("PM", na=False)]
                elif pollutant_group == "NOx":
                    filtered_stations = filtered_stations[filtered_stations["nometiposensore"].isin(["NO", "NO2", "NOx"])]
                elif pollutant_group == "Ozone":
                    filtered_stations = filtered_stations[filtered_stations["nometiposensore"] == "O3"]
            
            if province and province != "All":
                filtered_stations = filtered_stations[filtered_stations["provincia"] == province]
            
            if not filtered_stations.empty:
                # Create sensor distribution by province
                if len(filtered_stations['provincia'].unique()) > 1:
                    # Show distribution by province
                    province_counts = filtered_stations['provincia'].value_counts()
                    
                    fig = px.bar(
                        x=province_counts.index,
                        y=province_counts.values,
                        title="Sensor Distribution by Province",
                        labels={'x': 'Province', 'y': 'Number of Sensors'},
                        color_discrete_sequence=['rgb(19, 129, 159)']
                    )
                else:
                    # Show distribution by pollutant type when single province selected
                    pollutant_counts = filtered_stations['nometiposensore'].value_counts().head(10)
                    
                    fig = px.bar(
                        x=pollutant_counts.values,
                        y=pollutant_counts.index,
                        orientation='h',
                        title="Sensor Distribution by Pollutant Type",
                        labels={'x': 'Number of Sensors', 'y': 'Pollutant Type'},
                        color_discrete_sequence=['rgb(19, 129, 159)']
                    )
                
                fig.update_layout(
                    showlegend=False,
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    font=dict(size=12),
                    title_x=0.5,
                    margin=dict(l=50, r=50, t=50, b=50),
                    height=400
                )
                
                # Add total count annotation
                total_sensors = len(filtered_stations)
                fig.add_annotation(
                    text=f"Total Sensors: {total_sensors}",
                    xref="paper", yref="paper",
                    x=0.98, y=0.98,
                    xanchor="right", yanchor="top",
                    showarrow=False,
                    bgcolor="rgba(255,255,255,0.8)",
                    bordercolor="gray",
                    borderwidth=1,
                    font=dict(size=14, color="rgb(19, 129, 159)")
                )
            else:
                # No data after filtering
                fig = go.Figure()
                fig.add_annotation(
                    text="No sensors found for the selected filters",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    xanchor="center", yanchor="middle",
                    showarrow=False,
                    font=dict(size=16, color="gray")
                )
                fig.update_layout(
                    xaxis=dict(showgrid=False, showticklabels=False, title=""),
                    yaxis=dict(showgrid=False, showticklabels=False, title=""),
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    height=400
                )
        else:
            # Empty plot when no station data
            fig = go.Figure()
            fig.add_annotation(
                text="No sensor data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                xanchor="center", yanchor="middle",
                showarrow=False,
                font=dict(size=16, color="gray")
            )
            fig.update_layout(
                xaxis=dict(showgrid=False, showticklabels=False, title=""),
                yaxis=dict(showgrid=False, showticklabels=False, title=""),
                plot_bgcolor='white',
                paper_bgcolor='white',
                height=400
            )
    except Exception as e:
        # Error handling for sensor distribution chart
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error loading sensor data: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            xanchor="center", yanchor="middle",
            showarrow=False,
            font=dict(size=14, color="red")
        )
        fig.update_layout(
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False),
            plot_bgcolor='white',
            height=400
        )
    
    return sensor_map, station_info, fig
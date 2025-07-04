# pages/home_page.py
"""
Enhanced home page with sensor map, histogram display, and team section.
Improved with corrected pollutant groups and auto-centering map functionality.
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
from components.logger import logger

dash.register_page(__name__, path="/", name="Home")

# Province coordinates for map centering
PROVINCE_COORDINATES = {
    "MI": [45.4642, 9.1900],    # Milano
    "BG": [45.6983, 9.6773],    # Bergamo
    "BS": [45.5416, 10.2118],   # Brescia
    "CO": [45.8081, 9.0852],    # Como
    "CR": [45.1370, 10.0222],   # Cremona
    "LC": [45.8566, 9.3964],    # Lecco
    "LO": [45.3142, 9.5034],    # Lodi
    "MN": [45.1564, 10.7914],   # Mantova
    "MB": [45.5845, 9.2744],    # Monza e Brianza
    "PV": [45.1847, 9.1582],    # Pavia
    "SO": [46.1712, 9.8718],    # Sondrio
    "VA": [45.8205, 8.8250],    # Varese
    "NO": [45.4445, 8.7833],    # Novara *
    "RO": [45.0685, 11.7229],   # Rovigo *
    "VR": [45.4033, 10.9908]    # Verona *
}

# Get available provinces
def get_provinces():
    try:
        response = requests.get("http://localhost:5001/api/provinces")
        response.raise_for_status()
        data = response.json()
        
        df = pd.DataFrame(data, columns=["provincia"])
        logger.info("All provinces fetched successfully")
        return df["provincia"].dropna().tolist()
    
    except requests.RequestException as e:
        logger.error(f"Error fetching provinces: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return []

# Improved pollutant group filtering function
def filter_by_pollutant_group(df, pollutant_group):
    """Filter sensors by pollutant group with corrected categories"""
    if df.empty:
        return df
    
    # Normalize pollutant names for better matching
    df = df.copy()
    df["nometiposensore_normalized"] = df["nometiposensore"].str.strip().str.lower()

    if pollutant_group == "Particulate Matter":
        # PM10, PM2.5, and other particulate matter
        pm_keywords = ['pm10', 'particolato', 'particelle sospese', 'blackcarbon']
        mask = df["nometiposensore_normalized"].str.contains('|'.join(pm_keywords), na=False)
        return df[mask]
    
    elif pollutant_group == "Nitrogen Compounds":
        # NOx compounds (NO, NO2, NOx)
        nox_keywords = ['monossido di azoto', 'biossido di azoto', 'ossidi di azoto']
        mask = df["nometiposensore_normalized"].str.contains('|'.join(nox_keywords), na=False)
        return df[mask]
    
    elif pollutant_group == "Sulfur and Carbon Compounds":
        # Ozone compounds
        ozone_keywords = ['monossido di carbonio', 'biossido di zolfo']
        mask = df["nometiposensore_normalized"].str.contains('|'.join(ozone_keywords), na=False)
        return df[mask]
    
    elif pollutant_group == "Heavy Metals":
        # Sulfur dioxide and other sulfur compounds
        sulfur_keywords = ['arsenico', 'cadmio', 'nikel', 'piombo']
        mask = df["nometiposensore_normalized"].str.contains('|'.join(sulfur_keywords), na=False)
        return df[mask]
    
    elif pollutant_group == "Others":
        # Heavy metals and toxic compounds
        metals_keywords = ['benzene', 'benzo(a)pirene', 'Ozono']
        mask = df["nometiposensore_normalized"].str.contains('|'.join(metals_keywords), na=False)
        return df[mask]
    
    elif pollutant_group and pollutant_group != "All":
        # Exact match fallback
        return df[df["nometiposensore_normalized"] == pollutant_group.lower()]
    
    return df

def get_map_center_and_zoom(filtered_df, province=None):
    """Calculate appropriate map center and zoom level based on data"""
    
    if province and province != "All" and province in PROVINCE_COORDINATES:
        # Center on selected province
        return PROVINCE_COORDINATES[province], 9
    
    elif not filtered_df.empty and 'lat' in filtered_df.columns and 'lng' in filtered_df.columns:
        # Center on available data
        valid_coords = filtered_df.dropna(subset=['lat', 'lng'])
        if not valid_coords.empty:
            center_lat = valid_coords['lat'].mean()
            center_lng = valid_coords['lng'].mean()
            
            # Calculate zoom based on data spread
            lat_range = valid_coords['lat'].max() - valid_coords['lat'].min()
            lng_range = valid_coords['lng'].max() - valid_coords['lng'].min()
            max_range = max(lat_range, lng_range)
            
            if max_range < 0.1:
                zoom = 11
            elif max_range < 0.5:
                zoom = 10
            elif max_range < 1.0:
                zoom = 9
            else:
                zoom = 8
                
            return [center_lat, center_lng], zoom
    
    # Default to Lombardia center
    return [45.5, 9.2], 8

def create_filtered_map(pollutant_group=None, province=None):
    """Create map with filtered stations and automatic centering"""
    try:
        df_stations = fetch_pollutant()

        if df_stations.empty:
            center, zoom = get_map_center_and_zoom(pd.DataFrame(), province)
            return dl.Map(
                center=center,
                zoom=zoom,
                children=[dl.TileLayer(url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png")],
                style={"width": "100%", "height": "400px"}
            )
        
        logger.info("Filters pollutant group: %s, province: %s", pollutant_group, province)

        # Apply filters
        filtered = filter_by_pollutant_group(df_stations.copy(), pollutant_group)

        if province and province != "All":
            filtered = filtered[filtered["provincia"] == province]

        # Calculate map center and zoom
        center, zoom = get_map_center_and_zoom(filtered, province)

        # Group by station coordinates
        if not filtered.empty:
            grouped = filtered.groupby(["nomestazione", "lat", "lng"]).agg({
                "nometiposensore": list,
                "provincia": "first"
            }).reset_index()

            markers = []
            for _, row in grouped.iterrows():
                if pd.notna(row["lat"]) and pd.notna(row["lng"]):
                    # Create color-coded markers based on number of sensors
                    num_sensors = len(row["nometiposensore"])
                    
                    popup_content = [
                        html.H4(row["nomestazione"], style={"margin": "5px 0", "color": "#2c3e50"}),
                        html.P(f"Province: {row['provincia']}", style={"margin": "2px 0", "fontWeight": "bold"}),
                        html.P(f"Coordinates: {row['lat']:.4f}, {row['lng']:.4f}", style={"margin": "2px 0", "fontSize": "12px", "color": "#666"}),
                        html.P(f"Sensors: {num_sensors}", style={"margin": "5px 0", "fontWeight": "bold"}),
                        html.P("Pollutants:", style={"margin": "5px 0 2px 0", "fontWeight": "bold"}),
                        html.Ul([html.Li(p, style={"fontSize": "12px"}) for p in row["nometiposensore"]], 
                               style={"margin": "0", "paddingLeft": "20px", "maxHeight": "100px", "overflowY": "auto"})
                    ]
                    
                    markers.append(dl.Marker(
                        position=[row["lat"], row["lng"]],
                        children=dl.Popup(popup_content, maxWidth=300)
                    ))
        else:
            markers = []

        return dl.Map(
            center=center,
            zoom=zoom,
            children=[
                dl.TileLayer(url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"),
                dl.LayerGroup(markers, id="station-markers")
            ],
            style={"width": "100%", "height": "400px", "borderRadius": "8px"}
        )

    except Exception as e:
        logger.error(f"Error creating map: {e}")
        center, zoom = get_map_center_and_zoom(pd.DataFrame(), province)
        return dl.Map(
            center=center,
            zoom=zoom,
            children=[dl.TileLayer(url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png")],
            style={"width": "100%", "height": "400px"}
        )

### LAYOUT -> HOME PAGE ###
layout = html.Div([
    # Hero Section
    html.Div([
        html.Div([
            html.Img(
                src="/assets/logo.png", 
                style={
                    "height": "280px", 
                    "width": "280px", 
                    "marginBottom": "20px"
                }
            ),
            html.H1(
                "Welcome to GeoAir", 
                style={
                    "fontSize": "3.5rem", 
                    "marginBottom": "20px",
                    "color": "white",
                    "textShadow": "3px 3px 10px rgba(0,0,0,0.8)",
                    "margin": "0 auto 20px auto",
                    "width": "fit-content"
                }
            ),
            html.P(
                "Discover air quality evolution in Lombardia with historical data analysis and trend visualization", 
                style={
                    "fontSize": "1.3rem",
                    "color": "white",
                    "textShadow": "2px 2px 8px rgba(0,0,0,0.8)",
                    "maxWidth": "600px",
                    "margin": "0 auto 30px auto",
                    "lineHeight": "1.5",
                    "textAlign": "center"
                }
            ),
            html.Div([
                dcc.Link(
                    "Explore Map",
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
                    "View Trends",
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
        "background": "linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.5)), url('https://images.unsplash.com/photo-1506744038136-46273834b3fb')",
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
            "Interactive Air Quality Dashboard", 
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
                html.Label("Pollutant Group:", style={"fontWeight": "bold", "marginBottom": "8px", "display": "block"}),
                dcc.Dropdown(
                    id="pollutant-group-dropdown",
                    options=[
                        {"label": "All Pollutants", "value": "All"},
                        {"label": "Particulate Matter (PM)", "value": "Particulate Matter"},
                        {"label": "Nitrogen Compounds (NOx)", "value": "Nitrogen Compounds"},
                        {"label": "Sulfur and Carbon Compounds", "value": "Sulfur and Carbon Compounds"},
                        {"label": "Heavy Metals", "value": "Heavy Metals"},
                        {"label": "Others (Aromatic compounds and Ozone)", "value": "Others"}
                    ],
                    value="All",
                    clearable=False,
                    style={"fontSize": "14px"}
                )
            ], style={"flex": "1", "marginRight": "20px"}),
            
            html.Div([
                html.Label("Province:", style={"fontWeight": "bold", "marginBottom": "8px", "display": "block"}),
                dcc.Dropdown(
                    id="province-dropdown",
                    options=[{"label": "All Provinces", "value": "All"}] + 
                            [{"label": p, "value": p} for p in get_provinces()],
                    value="All",
                    clearable=False,
                    style={"fontSize": "14px"}
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
                html.H3("Station Locations", style={"color": "rgb(19, 129, 159)", "marginBottom": "15px"}),
                html.Div(id="sensor-map"),
                html.Div(id="station-info", style={
                    "marginTop": "10px", 
                    "color": "#666", 
                    "fontSize": "14px",
                    "padding": "10px",
                    "backgroundColor": "#f8f9fa",
                    "borderRadius": "5px",
                    "borderLeft": "4px solid rgb(19, 129, 159)"
                })
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
                html.H3("Sensor Distribution", style={"color": "rgb(19, 129, 159)", "marginBottom": "15px"}),
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

    # Updated Team Section for pages/home_page.py
    # Replace the existing team section (around line 280-350) with this code

    # Team Section with Profile Pictures
    html.Div([
        html.H2(
            "Meet Our Team", 
            style={
                "textAlign": "center", 
                "color": "white",
                "marginBottom": "50px",
                "fontSize": "2.5rem"
            }
        ),
        html.Div([
            # Team Member 1 - Gianluca Bettone
            html.Div([
                html.Div([
                    # Profile Picture or Initials
                    html.Img(
                        src="/assets/team/Gianluca.jpg",
                        style={
                            "width": "80px",
                            "height": "80px",
                            "borderRadius": "50%",
                            "backgroundColor": "rgba(255,255,255,0.3)",
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "center",
                            "color": "white",
                            "fontSize": "24px",
                            "fontWeight": "bold",
                            "border": "3px solid white",
                            "marginBottom": "20px",
                            "margin": "0 auto 20px auto"
                        }
                    ),
                    html.H3("Gianluca Bettoni", style={"color": "white", "margin": "0"})
                ], style={
                    "backgroundColor": "rgba(255,255,255,0.1)",
                    "padding": "30px",
                    "borderRadius": "15px",
                    "textAlign": "center",
                    "height": "160px",
                    "display": "flex",
                    "flexDirection": "column",
                    "justifyContent": "center"
                })
            ], style={"flex": "1", "margin": "0 15px"}),
            
            # Team Member 2 - Mobina Faraji
            html.Div([
                html.Div([
                    # Profile Picture or Initials
                    html.Img(
                        src="/assets/team/Mobina.jpeg",
                        style={
                            "width": "80px",
                            "height": "80px",
                            "borderRadius": "50%",
                            "backgroundColor": "rgba(255,255,255,0.3)",
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "center",
                            "color": "white",
                            "fontSize": "24px",
                            "fontWeight": "bold",
                            "border": "3px solid white",
                            "marginBottom": "20px",
                            "margin": "0 auto 20px auto"
                        }
                    ),
                    html.H3("Mobina Faraji", style={"color": "white", "margin": "0"})
                ], style={
                    "backgroundColor": "rgba(255,255,255,0.1)",
                    "padding": "30px",
                    "borderRadius": "15px",
                    "textAlign": "center",
                    "height": "160px",
                    "display": "flex",
                    "flexDirection": "column",
                    "justifyContent": "center"
                })
            ], style={"flex": "1", "margin": "0 15px"}),
            
            # Team Member 3 - Alessia Ippolito
            html.Div([
                html.Div([
                    # Profile Picture or Initials
                    html.Img(
                        src="/assets/team/Alessia.JPG",
                        style={
                            "width": "80px",
                            "height": "80px",
                            "borderRadius": "50%",
                            "backgroundColor": "rgba(255,255,255,0.3)",
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "center",
                            "color": "white",
                            "fontSize": "24px",
                            "fontWeight": "bold",
                            "border": "3px solid white",
                            "marginBottom": "20px",
                            "margin": "0 auto 20px auto"
                        }
                    ),
                    html.H3("Alessia Ippolito", style={"color": "white", "margin": "0"})
                ], style={
                    "backgroundColor": "rgba(255,255,255,0.1)",
                    "padding": "30px",
                    "borderRadius": "15px",
                    "textAlign": "center",
                    "height": "160px",
                    "display": "flex",
                    "flexDirection": "column",
                    "justifyContent": "center"
                })
            ], style={"flex": "1", "margin": "0 15px"}),
            
            # Team Member 4 - Edoardo Pessina
            html.Div([
                html.Div([
                    # Profile Picture or Initials
                    html.Img(
                        src="/assets/team/Edoardo.jpeg",
                        style={
                            "width": "80px",
                            "height": "80px",
                            "borderRadius": "50%",
                            "backgroundColor": "rgba(255,255,255,0.3)",
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "center",
                            "color": "white",
                            "fontSize": "24px",
                            "fontWeight": "bold",
                            "border": "3px solid white",
                            "marginBottom": "20px",
                            "margin": "0 auto 20px auto"
                        }
                    ),
                    html.H3("Edoardo Pessina", style={"color": "white", "margin": "0"})
                ], style={
                    "backgroundColor": "rgba(255,255,255,0.1)",
                    "padding": "30px",
                    "borderRadius": "15px",
                    "textAlign": "center",
                    "height": "160px",
                    "display": "flex",
                    "flexDirection": "column",
                    "justifyContent": "center"
                })
            ], style={"flex": "1", "margin": "0 15px"})
        ], style={
            "display": "flex",
            "maxWidth": "1200px",
            "margin": "0 auto",
            "flexWrap": "wrap",
            "gap": "20px"
        })
    ], style={
        "backgroundColor": "rgb(19, 129, 159)",
        "padding": "80px 20px",
        "marginTop": "40px"
    }),


])

# Callback to update the dashboard components based on selected filters
@callback(
    [Output("sensor-map", "children"),           # Update the sensor map component
     Output("station-info", "children"),        # Update the station info display
     Output("sensor-histogram", "figure")],     # Update the sensor histogram figure
    [Input("pollutant-group-dropdown", "value"),  # Trigger on pollutant group selection change
     Input("province-dropdown", "value")]          # Trigger on province selection change
)
def update_dashboard(pollutant_group, province):
    # Create the updated map filtered and auto-centered based on filters
    sensor_map = create_filtered_map(pollutant_group, province)

    # Fetch station data from API or database
    df_stations = fetch_pollutant()

    # === Station information section ===
    try:
        if not df_stations.empty:
            # Filter stations by selected pollutant group
            filtered = filter_by_pollutant_group(df_stations.copy(), pollutant_group)
            # If a specific province is selected (other than "All"), filter by it as well
            if province and province != "All":
                filtered = filtered[filtered["provincia"] == province]
            
            # Count unique stations and total number of sensors after filtering
            num_stations = filtered["nomestazione"].nunique()
            num_sensors = len(filtered)
            
            # Prepare station info display text with details
            if province and province != "All":
                # Show station and sensor count for selected province
                station_info = html.Div([
                    html.Span(f"{num_stations} stations with {num_sensors} sensors in {province}", style={"fontWeight": "bold"}),
                    html.Br(),
                    # Commented out optional message about map centering
                    # html.Span("Map automatically centered on selected province", style={"fontSize": "12px", "color": "#666", "fontStyle": "italic"})
                ])
            else:
                # Show counts across all provinces
                station_info = html.Div([
                    html.Span(f"{num_stations} stations with {num_sensors} sensors across all provinces", style={"fontWeight": "bold"})
                ])
        else:
            # Handle case when no station data is available
            station_info = "No station data available"
    except Exception as e:
        # Handle errors during station info fetching
        station_info = f"Error loading station info: {e}"

    # === Enhanced sensor histogram section ===
    try:
        if df_stations.empty:
            raise ValueError("Empty station dataset")

        # Filter by pollutant group and province as before
        filtered = filter_by_pollutant_group(df_stations.copy(), pollutant_group)
        if province and province != "All":
            filtered = filtered[filtered["provincia"] == province]

        if not filtered.empty:
            # If multiple provinces present, show sensor distribution by province
            if len(filtered["provincia"].unique()) > 1:
                counts = filtered["provincia"].value_counts()
                fig = px.bar(
                    x=counts.index,
                    y=counts.values,
                    title="Sensor Distribution by Province",
                    labels={"x": "Province", "y": "Number of Sensors"},
                    color_discrete_sequence=["rgb(19, 129, 159)"]
                )
            else:
                # If single province, show sensor distribution by pollutant type
                counts = filtered["nometiposensore"].value_counts().head(10)
                fig = px.bar(
                    x=counts.values,
                    y=counts.index,
                    orientation="h",
                    title="Sensor Distribution by Pollutant Type",
                    labels={"x": "Number of Sensors", "y": "Pollutant Type"},
                    color_discrete_sequence=["rgb(19, 129, 159)"]
                )

            # Customize layout for better visualization
            fig.update_layout(
                showlegend=False,
                plot_bgcolor="white",
                paper_bgcolor="white",
                font=dict(size=12),
                title_x=0.5,
                margin=dict(l=50, r=50, t=50, b=50),
                height=400
            )

            # Add annotation with pollutant group info and total sensors
            pollutant_text = f"Group: {pollutant_group}" if pollutant_group != "All" else "All Groups"
            fig.add_annotation(
                text=f"Total Sensors: {len(filtered)}<br>{pollutant_text}",
                xref="paper", yref="paper",
                x=0.98, y=0.98,
                xanchor="right", yanchor="top",
                showarrow=False,
                bgcolor="rgba(255,255,255,0.9)",
                bordercolor="rgb(19, 129, 159)",
                borderwidth=2,
                font=dict(size=12, color="rgb(19, 129, 159)")
            )
        else:
            # Raise error if no sensors found matching filters
            raise ValueError("No sensors found for the selected filters")

    except Exception as e:
        # If error or no data, return empty figure with error message
        fig = go.Figure()
        fig.add_annotation(
            text=f"No sensor data available<br>{str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            xanchor="center", yanchor="middle",
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False),
            plot_bgcolor="white",
            paper_bgcolor="white",
            height=400
        )

    # Return the updated map, station info text, and histogram figure
    return sensor_map, station_info, fig

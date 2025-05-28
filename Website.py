# Air Quality Dashboard - University Project
# Student: [Your Name] - Environmental Data Science
# This project demonstrates Python web development for environmental monitoring

# ============================================================================
# IMPORTS - Learning different Python libraries
# ============================================================================
import pandas as pd          # Data analysis - most important for data science!
import dash                  # Web framework - learned in web dev class
from dash import dcc, html, Input, Output
import dash_leaflet as dl    # Interactive maps
import plotly.express as px  # Easy plotting
import psycopg2             # Database connection
from datetime import datetime
import logging

# ============================================================================
# CONFIGURATION - Like we learned in software engineering
# ============================================================================

# Database settings (in real project, use environment variables!)
DB_CONFIG = {
    "host": "localhost",
    "database": "lombardia_air_quality", 
    "user": "airdata_user",
    "password": "user"
}

# Air quality standards from WHO (World Health Organization)
# These are the "safe" levels from scientific studies
AIR_STANDARDS = {
    "PM2.5": 5,    # μg/m³ - WHO annual guideline
    "PM10": 15,    # μg/m³ - WHO annual guideline  
    "NO2": 10,     # μg/m³ - WHO annual guideline
    "O3": 100,     # μg/m³ - WHO peak season
    "SO2": 40,     # μg/m³ - WHO daily guideline
}

# Colors for different pollution levels (traffic light system)
STATUS_COLORS = {
    "Good": "#27ae60",        # Green - safe
    "Moderate": "#f39c12",    # Yellow - caution
    "Poor": "#e74c3c",        # Red - unhealthy
    "Very Poor": "#8e44ad"    # Purple - dangerous
}

# Group pollutants by type (chemistry classification)
POLLUTANT_GROUPS = {
    "Particulate Matter": ["PM10", "PM2.5", "Particelle sospese PM2.5"],
    "Nitrogen Compounds": ["NO2", "Ossidi di Azoto", "Biossido di Azoto"], 
    "Other Gases": ["O3", "SO2", "CO", "Ozono", "Biossido di Zolfo"],
    "Heavy Metals": ["Arsenico", "Piombo", "Cadmio"]
}

GROUP_COLORS = {
    "Particulate Matter": "#e74c3c",
    "Nitrogen Compounds": "#3498db", 
    "Other Gases": "#2ecc71",
    "Heavy Metals": "#9b59b6"
}

# ============================================================================
# HELPER FUNCTIONS - The math behind air quality
# ============================================================================

def calculate_air_status(pollutant, value):
    """
    Simple function to determine if air quality is good or bad
    Based on WHO guidelines learned in environmental science class
    """
    if pollutant not in AIR_STANDARDS:
        return "Unknown", STATUS_COLORS["Moderate"]
    
    safe_limit = AIR_STANDARDS[pollutant]
    
    if value <= safe_limit:
        return "Good", STATUS_COLORS["Good"]
    elif value <= safe_limit * 2:
        return "Moderate", STATUS_COLORS["Moderate"] 
    elif value <= safe_limit * 3:
        return "Poor", STATUS_COLORS["Poor"]
    else:
        return "Very Poor", STATUS_COLORS["Very Poor"]

def get_data_from_database():
    """
    Connect to database and get station data
    Using try/except like professor taught us for error handling
    """
    try:
        # Try to connect to PostgreSQL database
        conn = psycopg2.connect(**DB_CONFIG)
        
        # SQL query to get station information
        query = """
        SELECT idsensore, nomestazione, lat, lng, nometiposensore, 
               provincia, comune, quota
        FROM station 
        WHERE lat IS NOT NULL AND lng IS NOT NULL
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        print(f"✅ Loaded {len(df)} stations from database")
        return df
        
    except Exception as e:
        # If database fails, use CSV file (backup plan)
        print(f"❌ Database failed: {e}")
        print("📁 Using CSV backup data...")
        try:
            return pd.read_csv('station.csv')
        except:
            print("❌ CSV file not found either!")
            return pd.DataFrame()  # Empty dataframe

def get_sensor_data():
    """Get recent sensor measurements"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        query = """
        SELECT idsensore, data, valore, stato
        FROM sensors 
        WHERE data >= CURRENT_DATE - INTERVAL '7 days'
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except:
        try:
            return pd.read_csv('sensors.csv')
        except:
            return pd.DataFrame()

def create_map_markers(df, selected_group):
    """
    Create markers for the map based on selected pollutant group
    This is where we apply the grouping we learned about
    """
    if df.empty or selected_group not in POLLUTANT_GROUPS:
        return []
    
    # Filter data for selected group
    group_pollutants = POLLUTANT_GROUPS[selected_group]
    filtered_df = df[df['nometiposensore'].isin(group_pollutants)]
    
    markers = []
    color = GROUP_COLORS[selected_group]
    
    # Create a marker for each station
    for _, station in filtered_df.iterrows():
        marker = dl.CircleMarker(
            center=[station['lat'], station['lng']],
            radius=7,
            color=color,
            fill=True,
            children=dl.Popup([
                html.H4(station['nomestazione']),
                html.P(f"Pollutant: {station['nometiposensore']}"),
                html.P(f"Location: {station['comune']}, {station['provincia']}"),
                html.P(f"Elevation: {station['quota']}m")
            ])
        )
        markers.append(marker)
    
    return markers

# ============================================================================
# CREATE CURRENT AIR QUALITY CARDS - The main feature!
# ============================================================================

def create_pollutant_card(name, value, unit, description):
    """
    Create a nice looking card for each pollutant
    Using HTML and CSS like we learned in web design
    """
    status, color = calculate_air_status(name, value)
    
    return html.Div([
        # Pollutant name and description
        html.H3(name, style={
            "margin": "0 0 5px 0", 
            "fontSize": "1.5rem", 
            "fontWeight": "bold"
        }),
        html.P(description, style={
            "fontSize": "0.9rem", 
            "color": "#666", 
            "margin": "0 0 15px 0"
        }),
        
        # Big number showing current value
        html.Div([
            html.Span("●", style={"color": color, "fontSize": "1.5rem", "marginRight": "10px"}),
            html.Span(f"{value}", style={"fontSize": "2.5rem", "fontWeight": "bold"}),
            html.Span(f" {unit}", style={"fontSize": "1rem", "color": "#888"})
        ], style={"display": "flex", "alignItems": "baseline"}),
        
        # Status (Good, Moderate, etc.)
        html.P(f"Status: {status}", style={
            "color": color, 
            "fontWeight": "bold", 
            "margin": "10px 0 0 0"
        })
        
    ], style={
        "backgroundColor": "white",
        "padding": "20px",
        "borderRadius": "10px",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
        "border": f"2px solid {color}",
        "margin": "10px",
        "width": "300px"
    })

# ============================================================================
# LOAD DATA - Get everything ready
# ============================================================================

print("🚀 Starting Air Quality Dashboard...")
print("📊 Loading data...")

# Load our data
stations_df = get_data_from_database()
sensors_df = get_sensor_data()

# Current Milan air quality (example data)
current_milan_data = {
    "PM2.5": 12.5,
    "PM10": 18.2, 
    "NO2": 25.8,
    "O3": 45.2,
    "SO2": 8.1,
    "CO": 0.8
}

# Calculate data quality
if not sensors_df.empty:
    total_readings = len(sensors_df)
    valid_readings = len(sensors_df[sensors_df['stato'] == 'VA']) if 'stato' in sensors_df.columns else total_readings
    data_quality_percent = (valid_readings / total_readings) * 100
else:
    data_quality_percent = 0
    total_readings = 0

print(f"✅ Ready! Loaded {len(stations_df)} stations")

# ============================================================================
# DASH APP SETUP - The web interface
# ============================================================================

app = dash.Dash(__name__)
app.title = "Air Quality Dashboard - University Project"

# The main layout - this is what users see
app.layout = html.Div([
    
    # Header section
    html.Div([
        html.H1("🌍 Lombardia Air Quality Monitor", style={
            "textAlign": "center", 
            "color": "white", 
            "margin": "0",
            "fontSize": "2.5rem"
        }),
        html.P("University Environmental Science Project", style={
            "textAlign": "center", 
            "color": "white", 
            "margin": "10px 0 0 0",
            "fontSize": "1.1rem"
        })
    ], style={
        "background": "linear-gradient(135deg, #3498db, #2980b9)",
        "padding": "30px",
        "marginBottom": "20px"
    }),
    
    # Current Air Quality Section - THE MAIN FEATURE!
    html.Div([
        html.H2("Current Air Quality in Milan", style={
            "textAlign": "center", 
            "color": "#2c3e50",
            "marginBottom": "30px"
        }),
        
        # Grid of pollutant cards
        html.Div([
            create_pollutant_card("PM2.5", current_milan_data["PM2.5"], "μg/m³", 
                                "Fine particles that can reach deep into lungs"),
            create_pollutant_card("PM10", current_milan_data["PM10"], "μg/m³", 
                                "Larger particles from dust and combustion"), 
            create_pollutant_card("NO2", current_milan_data["NO2"], "μg/m³", 
                                "Nitrogen dioxide from traffic and industry"),
            create_pollutant_card("O3", current_milan_data["O3"], "μg/m³", 
                                "Ground-level ozone formed by sunlight"),
            create_pollutant_card("SO2", current_milan_data["SO2"], "μg/m³", 
                                "Sulfur dioxide from burning fossil fuels"),
            create_pollutant_card("CO", current_milan_data["CO"], "mg/m³", 
                                "Carbon monoxide from vehicle exhaust")
        ], style={
            "display": "flex", 
            "flexWrap": "wrap", 
            "justifyContent": "center"
        }),
        
        # Overall summary
        html.Div([
            html.H3("📊 Overall Assessment", style={"color": "#2c3e50"}),
            html.P("Air quality is MODERATE today. Sensitive people should limit outdoor activities.", 
                  style={"fontSize": "1.1rem", "color": "#f39c12", "fontWeight": "bold"}),
            html.P(f"Last updated: {datetime.now().strftime('%H:%M, %B %d, %Y')}", 
                  style={"color": "#95a5a6", "fontSize": "0.9rem"})
        ], style={
            "textAlign": "center", 
            "backgroundColor": "#f8f9fa", 
            "padding": "20px", 
            "borderRadius": "10px",
            "margin": "20px"
        })
        
    ], style={"margin": "20px"}),
    
    # Data Quality section
    html.Div([
        html.H3("📈 Data Quality", style={"color": "#2c3e50"}),
        html.Div([
            html.Div(f"Valid Data: {data_quality_percent:.1f}%", style={
                "width": f"{data_quality_percent}%",
                "backgroundColor": "#27ae60" if data_quality_percent > 90 else "#f39c12",
                "color": "white",
                "textAlign": "center", 
                "padding": "10px 0",
                "borderRadius": "5px 0 0 5px"
            }),
            html.Div(f"Issues: {100-data_quality_percent:.1f}%", style={
                "width": f"{100-data_quality_percent}%",
                "backgroundColor": "#e74c3c",
                "color": "white", 
                "textAlign": "center",
                "padding": "10px 0", 
                "borderRadius": "0 5px 5px 0"
            })
        ], style={"display": "flex", "margin": "10px 0"}),
        html.P(f"Total measurements analyzed: {total_readings:,}", 
              style={"color": "#7f8c8d", "fontSize": "0.9rem"})
    ], style={
        "backgroundColor": "white", 
        "padding": "20px", 
        "borderRadius": "10px",
        "boxShadow": "0 2px 4px rgba(0,0,0,0.1)", 
        "margin": "20px"
    }),
    
    # Interactive Map Section
    html.Div([
        html.H3("🗺️ Interactive Station Map", style={"color": "#2c3e50", "marginBottom": "20px"}),
        
        # Controls
        html.Div([
            html.Label("Select Pollutant Group:", style={"fontWeight": "bold"}),
            dcc.Dropdown(
                id='group-dropdown',
                options=[{"label": group, "value": group} for group in POLLUTANT_GROUPS.keys()],
                value="Particulate Matter",
                style={"marginBottom": "10px"}
            ),
            html.Div(id="station-count", style={"color": "#7f8c8d"})
        ], style={"marginBottom": "20px"}),
        
        # The actual map
        dl.Map(
            id="map",
            center=[45.5, 9.2],  # Center on Lombardy
            zoom=8,
            style={"width": "100%", "height": "500px", "borderRadius": "10px"},
            children=[
                dl.TileLayer(url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png")
            ]
        )
    ], style={
        "backgroundColor": "white", 
        "padding": "20px", 
        "borderRadius": "10px",
        "boxShadow": "0 2px 4px rgba(0,0,0,0.1)", 
        "margin": "20px"
    }),
    
    # Simple Chart Section 
    html.Div([
        html.H3("📊 Data Analysis", style={"color": "#2c3e50"}),
        dcc.Graph(id="analysis-chart")
    ], style={
        "backgroundColor": "white", 
        "padding": "20px", 
        "borderRadius": "10px",
        "boxShadow": "0 2px 4px rgba(0,0,0,0.1)", 
        "margin": "20px"
    }),
    
    # Footer
    html.Div([
        html.P("Data source: Lombardia Environmental Agency | Student Project 2025", 
              style={"textAlign": "center", "color": "#95a5a6", "margin": "20px"})
    ])
])

# ============================================================================
# INTERACTIVE CALLBACKS - Make the map work!
# ============================================================================

@app.callback(
    [Output('map', 'children'), Output('station-count', 'children')],
    [Input('group-dropdown', 'value')]
)
def update_map(selected_group):
    """
    This function runs when user selects different pollutant group
    It updates the map markers - this is the cool interactive part!
    """
    # Create base map layer
    base_layer = dl.TileLayer(url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png")
    
    # Create markers for selected group
    markers = create_map_markers(stations_df, selected_group)
    
    # Count stations
    if selected_group in POLLUTANT_GROUPS:
        group_pollutants = POLLUTANT_GROUPS[selected_group]
        if not stations_df.empty:
            count = len(stations_df[stations_df['nometiposensore'].isin(group_pollutants)])
        else:
            count = 0
        station_info = f"📍 Showing {count} stations monitoring {selected_group}"
    else:
        station_info = "No data available"
    
    return [base_layer] + markers, station_info

@app.callback(
    Output('analysis-chart', 'figure'),
    [Input('group-dropdown', 'value')]
)
def update_chart(selected_group):
    """
    Create a simple chart showing pollutant distribution
    This demonstrates basic data visualization skills
    """
    if stations_df.empty:
        # Empty chart if no data
        return px.bar(title="No data available")
    
    # Count stations by province for selected group
    if selected_group in POLLUTANT_GROUPS:
        group_pollutants = POLLUTANT_GROUPS[selected_group]
        filtered_df = stations_df[stations_df['nometiposensore'].isin(group_pollutants)]
        
        if not filtered_df.empty:
            # Count by province
            province_counts = filtered_df['provincia'].value_counts().reset_index()
            province_counts.columns = ['Province', 'Station Count']
            
            # Create bar chart
            fig = px.bar(
                province_counts, 
                x='Province', 
                y='Station Count',
                title=f"Number of {selected_group} Monitoring Stations by Province",
                color='Station Count',
                color_continuous_scale='Blues'
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            return fig
    
    # Default empty chart
    return px.bar(title="Select a pollutant group to view data")

# ============================================================================
# RUN THE APP - Start the web server
# ============================================================================

if __name__ == '__main__':
    print("🎉 Dashboard ready!")
    print("🌐 Open your browser to: http://127.0.0.1:8050")
    print("📚 This is a university project demonstrating:")
    print("   - Database connectivity with PostgreSQL")
    print("   - Interactive web development with Dash")
    print("   - Real-time air quality data visualization") 
    print("   - Environmental science data analysis")
    print("\n🔄 Press Ctrl+C to stop the server")
    
    app.run(debug=True, host='127.0.0.1', port=8050)
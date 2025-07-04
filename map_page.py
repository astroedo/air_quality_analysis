import dash
import requests
import pandas as pd
from components.logger import logger
from dash import dcc
from dash import html, Output, Input, State, no_update
from components.dropdown_component import create_dropdown
from components.fetch_pollutant import fetch_pollutant
import plotly.express as px
from datetime import datetime
import geopandas as gpd
import dash_leaflet as dl
from uuid import uuid4
import os 
import zipfile
import io

province = gpd.read_file('maps/Lombardy_admin2.shp') #shapefile of Lombardy adimn 2 (provinces)
province = province.to_crs(epsg=4326)  #apply the rigth CRS

dash.register_page(__name__, path="/map", name="Map")

# funcion to create the dataframe with pollutants for the dropdown
df_all = fetch_pollutant()
pollutants = sorted(df_all["nometiposensore"].dropna().unique()) if not df_all.empty else []

# layout of the map page
layout = html.Div([
    # Store component to manage session data login state
    
    html.Div(id="redirect-map"),

    # Page titles
    html.H2("Air Quality Map", 
            style={"textAlign": "center",
                "color": "rgb(19, 129, 159)",
                "fontSize": "32px",
                "marginBottom": "10px", 
                "marginTop": "40px"}),
    html.H3("Average Pollutant Levels by Province", 
            style={"textAlign": "center",
            "color": "#7f8c8d",
            "fontSize": "16px",
            "marginBottom": "20px", 
            "fontWeight": "normal"}),

    # Output area for messages
    html.Div(
        id='graph-output',
        style={
            'textAlign': 'center',
            'marginTop': '10px',
            'marginBottom': '50px',
            'color': 'red',
            'fontWeight': 'bold'
        }
    ),

    html.Div([
        # Map container
        html.Div([
            # Leaflet map
            dl.Map(
                id="leaflet-map",
                center=[45.5, 9.2],
                zoom=7,
                children=[
                    dl.TileLayer(id="base-layer"),
                    dl.LayerGroup(id="layer-province")
                ],
                style={"width": "100%", "height": "600px"}
            ),

            # Download shapefile button
            html.Button(
                "Download Shapefile",
                id="btn-download-shp",
                style={
                    "position": "absolute",
                    "bottom": "20px",
                    "right": "20px",
                    "zIndex": 1000,
                    "color": "white",
                    "height": "40px",
                    "borderRadius": "8px",
                    "padding": "10px 20px",
                    "backgroundColor": "#007BFF",
                    "border": "none",
                    "cursor": "pointer",
                    "fontWeight": "bold",
                    "boxShadow": "0 2px 8px rgba(0,0,0,0.3)"
                }
            ),
            dcc.Download(id="download-shp"),

            # Pollutant dropdown selector
            create_dropdown(pollutants, show_all=False),

            # Date range picker
            dcc.DatePickerRange(
                id="date-picker-range",
                min_date_allowed=datetime(2024, 1, 1),
                max_date_allowed=datetime(2025, 1, 1),
                start_date=datetime(2024, 12, 1),
                end_date=datetime(2024, 12, 31),
                display_format="DD/MM/YYYY",
                style={
                    "position": "absolute",
                    "top": "10px",
                    "left": "100px",
                    "zIndex": 800,
                    "backgroundColor": "white",
                    "display": "flex",
                    "borderRadius": "8px",
                    "boxShadow": "0 2px 8px rgba(0,0,0,0.3)",
                    "marginTop": "10px",
                    "cursor": "pointer",
                }
            )
        ], style={"position": "relative"}),

        # Map legend container
        html.Div(
            id="map-legend",
            style={
                "position": "absolute",
                "bottom": "20px",
                "left": "20px",
                "width": "150px",
                "backgroundColor": "white",
                "zIndex": 1000,
                "fontSize": "14px",
                "padding": "10px",
                "boxShadow": "0 2px 8px rgba(0,0,0,0.3)",
                "borderRadius": "8px",
                "display": "none"
            }
        )
    ], style={
        "position": "relative",
        "borderRadius": "15px",
        "overflow": "hidden",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.2)",
        "marginBottom": "30px"
    }),

    # Histogram chart
    html.Div([
        dcc.Graph(
            id="histogram",
            style={"height": "400px"}
        )
    ])
], style={
    "paddingLeft": "20px",
    "paddingRight": "20px",
    "maxWidth": "1200px",
    "margin": "auto"
})




# Function to fetch average pollutant for provinces and time range
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
    except Exception as e: # if there is an error in the API request, log the error and return an empty DataFrame
        logger.error(f"Error fetching data: {e}")
        return pd.DataFrame()

# Function to create the province layer with colors based on pollutant values and create the legend
def create_province_layer_legend(df_pollutant):
    """
    Creates a Dash Leaflet FeatureGroup with colored provinces based on pollutant levels,
    and generates a corresponding legend.

    Parameters:
        df_pollutant (DataFrame): DataFrame with columns 'provincia' and 'mean' containing
                                  average pollutant levels per province.

    Returns:
        Tuple:
            - dl.FeatureGroup: Leaflet polygons colored by pollution values
            - list[html.Div]: HTML legend elements
            - GeoDataFrame: GeoDataFrame merged with pollution data and color mapping
    """

    # Mapping province names (in shapefile) to abbreviations (used in database)
    nome_to_sigla = {
        "Milano": "MI", "Bergamo": "BG", "Brescia": "BS",
        "Como": "CO", "Cremona": "CR", "Lecco": "LC",
        "Lodi": "LO", "Mantua": "MN", "Monza and Brianza": "MB",
        "Pavia": "PV", "Sondrio": "SO", "Varese": "VA"
    }

    # Add the province abbreviation to the shapefile
    province["sigla"] = province["NAME_2"].map(nome_to_sigla)

    # Join the shapefile with the pollutant data by province abbreviation
    gdf = province.merge(df_pollutant, left_on="sigla", right_on="provincia", how="left")

    # Determine the min and max pollution values
    min_val = gdf["mean"].min()
    max_val = gdf["mean"].max()

    if pd.isna(min_val) or pd.isna(max_val):
        # If values are missing or undefined, return an empty layer
        logger.warning("Pollution data missing or incomplete. Returning empty layers.")
        return [], [], gdf

    # Color function from green to yellow to red based on normalized pollution values
    def get_color(val):
        if pd.isna(val):
            return "#cccccc"  # Gray for missing values
        if max_val - min_val < 1e-6:
            norm = 0.5  # If all values are identical, use middle of scale
        else:
            norm = (val - min_val) / (max_val - min_val)
        if norm < 0.5:
            # Green to yellow
            r = int(255 * norm * 2)
            g = 255
        else:
            # Yellow to red
            r = 255
            g = int(255 * (1 - norm) * 2)
        b = 0
        return f"#{r:02x}{g:02x}{b:02x}"

    # Create legend intervals
    legend_values = [min_val + i * (max_val - min_val) / 4 for i in range(5)]
    legend_ranges = [(legend_values[i], legend_values[i + 1]) for i in range(4)]
    legend_colors = [get_color((r[0] + r[1]) / 2) for r in legend_ranges]

    # Build HTML legend elements
    legend_elements = [html.P("Pollution Level", style={"margin": "0 0 10px 0", "fontWeight": "bold"})]
    for (min_r, max_r), color in zip(legend_ranges, legend_colors):
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
                html.Span(f"{min_r:.1f} - {max_r:.1f}", style={"verticalAlign": "top"})
            ], style={"display": "flex", "alignItems": "center", "margin": "3px 0"})
        )

    # Add "No data" to the legend
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

    # Discrete color assignment for each province based on ranges
    def get_color_discrete(val, ranges, colors):
        if pd.isna(val):
            return "#cccccc"
        for (min_r, max_r), color in zip(ranges, colors):
            if min_r <= val <= max_r:
                return color
        return colors[-1]

    # Assign colors and tooltips to the GeoDataFrame
    gdf["color"] = [get_color_discrete(val, legend_ranges, legend_colors) for val in gdf["mean"]]
    gdf["tooltip"] = gdf.apply(
        lambda row: f"{row['NAME_2']}: {row['mean']:.2f}" if pd.notna(row["mean"]) else f"{row['NAME_2']}: No data",
        axis=1
    )

    # Create Leaflet polygons for each province
    polygons = []
    for _, row in gdf.iterrows():
        geom = row["geometry"]
        coords = []
        if geom.geom_type == 'Polygon':
            coords = [[[lat, lon] for lon, lat in geom.exterior.coords]]
        elif geom.geom_type == 'MultiPolygon':
            coords = [[[lat, lon] for lon, lat in poly.exterior.coords] for poly in geom.geoms]

        polygon = dl.Polygon(
            id=f"poly-{uuid4()}",
            positions=coords,
            fillColor=row["color"],
            fillOpacity=0.7,
            color="black",
            weight=1,
            children=[dl.Tooltip(children=row["tooltip"], permanent=False, sticky=True)]
        )
        polygons.append(polygon)
    
    logger.info("Province layer legend created successfully.")

    # Return map layer, legend, and enriched GeoDataFrame
    return dl.FeatureGroup(children=polygons), legend_elements, gdf



# Callback to update the map and histogram based on the selected pollutant and date range
@dash.callback(
    [Output("histogram", "figure"),
     Output("histogram", "style"), # style to show/hide the histogram
     Output("graph-output", "children"), # message to show when no pollutant is selected
     Output("layer-province", "children"), # layer of the map with the provinces
     Output("map-legend", "children"), 
     Output("map-legend", "style"), # style of the legend show/hide
     Output("redirect-map", "children")], # redirect to login if not logged in
    [Input("pollutant-selector", "value"), # pollutant selected from the dropdown
     Input("date-picker-range", "start_date"), # start date from the date picker
     Input("date-picker-range", "end_date"),
     Input("session", "data")] # session data to check if the user is logged in
)
def update_all(selected_pollutant, start_date, end_date, session_data):
    
    # convert start_date and end_date to datetime objects if they are provided
    if start_date:
        start_date = datetime.fromisoformat(start_date)
    if end_date:
        end_date = datetime.fromisoformat(end_date)

    # Check if the user is logged in, if not redirect to login page
    if not session_data or not session_data.get("logged_in"):
        return {}, {'display': 'none'}, "Please login.", [], [], {"display": "none"}, dcc.Location(href="/login", id="redirect-now")
    else:
        try:
            if selected_pollutant is None: # if no pollutant is selected, print a message and hide the histogram
                legend_style = {"display": "none"}
                return {}, {'display': 'none'}, "Please select a pollutant to view the map and the histogram below.", [], [], legend_style, no_update
            
            # Fetch the average pollutant data for the selected pollutant and date range
            df = fetch_avg_province_pollutant(selected_pollutant, start_date, end_date)
            if df.empty: # if the dataframe is empty, print a message and hide the histogram
                legend_style = {"display": "none"}
                return {}, {'display': 'none'}, "No data available for the selected pollutant and date range.", [], [], legend_style, no_update
            else:
                # create the province layer and legend
                layer, legend, _ = create_province_layer_legend(df)
                legend_style ={
                    "position": "absolute",         
                "bottom": "20px",               
                "left": "20px",                 
                "width": "150px",
                "backgroundColor": "white",
                "zIndex": "1000",
                "fontSize": "14px",
                "padding": "10px",
                "boxShadow": "0 2px 8px rgba(0,0,0,0.3)",
                "borderRadius": "8px",
                "display": "block"  }       

                # Create the histogram figure using Plotly Express
                unit = df["unitamisura"].iloc[0] if "unitamisura" in df.columns else ""
                fig = px.bar(
                    df,
                    x="provincia",
                    y="mean", 
                    title=f"Average '{selected_pollutant}' per Province in {unit}",
                    labels={"provincia": "Province", "mean": "Average Value"},
                    template="plotly_white",  
                    color_discrete_sequence=["rgb(19, 129, 159)"]
                )
                fig.update_layout( # update the layout of the figure
                    xaxis_title="Province",
                    yaxis_title=f"Average {selected_pollutant} ({unit})",
                    title_x=0.5,
                    title={
                    'text': fig.layout.title.text,  # mantiene il testo attuale del titolo
                    'font': {'size': 24, 'family': 'Arial', 'color': 'black', 'weight': 'bold'}}
                )
                logger.info(f"Updating map layer with {len(layer.children)} polygons")
                if not start_date or not end_date:
                    return fig, {'display': 'block'}, "Showing the last 7 days average. Else insert a time range", layer.children, legend, legend_style, no_update
                return fig, {'display': 'block'}, "", layer.children, legend, legend_style, no_update
        
        except Exception as e: # if there is an error in the callback, print the error and hide the histogram
            legend_style = {"display": "none"}
            return {}, {"display": "none"}, f"Errore: {str(e)}", [], [], legend_style, no_update
        
# Callback to generate and download the shapefile of the map with the selected pollutant
@dash.callback(
    Output("download-shp", "data"), # output to download the shapefile
    Input("btn-download-shp", "n_clicks"), # button to download the shapefile
    [State("pollutant-selector", "value"),
     State("date-picker-range", "start_date"),
     State("date-picker-range", "end_date")],
    prevent_initial_call=True, # prevent the callback from being called on page load
)
def genera_shapefile(n_clicks, selected_pollutant, start_date, end_date):

    if not selected_pollutant: # if no pollutant is selected, do not generate the shapefile
        return dash.no_update
    try:
        df = fetch_avg_province_pollutant(selected_pollutant, start_date, end_date)
        if df.empty: # if the dataframe is empty, do not generate the shapefile
            return dash.no_update
        # create the province layer and legend
        _, _, gdf = create_province_layer_legend(df)

        temp_dir = "temp_shp" # temporary directory to store the shapefile
        os.makedirs(temp_dir, exist_ok=True) # create the directory if it does not exist

        gdf.to_file(os.path.join(temp_dir, "GeoAir_map.shp")) # save the GeoDataFrame to a shapefile

        zip_buffer = io.BytesIO() # create a buffer to store the zip file
        # Create a zip file in memory
        with zipfile.ZipFile(zip_buffer, "w") as zipf:
            for fname in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, fname)
                zipf.write(file_path, arcname=fname)
        # Clean up the temporary directory
        for fname in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, fname))
        os.rmdir(temp_dir)

        zip_buffer.seek(0) # reset the buffer position to the beginning
        return dcc.send_bytes(zip_buffer.read(), filename="GeoAir_map.zip")

    except Exception as e: # if there is an error in the shapefile generation, print the error and return no update
        logger.error(f"Error in the shapefile download: {e}")
        return dash.no_update


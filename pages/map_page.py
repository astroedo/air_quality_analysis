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
    dcc.Store(id="session", storage_type="session"),
    html.Div(id="redirect-map"),
    # Header of the page
    html.H1("Air Quality Map", style={ "textAlign": "center", "color": "rgb(19, 129, 159)", "marginBottom": "10px", "fontSize": "32px" }),
    html.H2("Average Pollutant Levels by Province", style={"textAlign": "center", "marginBottom": "20px"}),
    html.Div(id='graph-output', style={'textAlign': 'center', 'marginTop': '10px', 'marginBottom': '50px', 'color': 'red', 'fontWeight': 'bold'}),
    html.Div([  
        html.Div([  # map container
            # map with leaflet
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
            html.Button("Download Shapefile", id="btn-download-shp", # button to download the shapefile
                        style ={ "position": "absolute",
                                 "bottom": "20px",
                                "right": "20px",
                                "zIndex": 1000,
                                "color": "white",
                                "height": "40px",
                                "borderRadius": "8px",  
                                "padding": "10px 20px", # internal spacing
                                "backgroundColor": "#007BFF",  
                                "border": "none",
                                "cursor": "pointer",
                                "fontWeight": "bold",
                                "boxShadow": "0 2px 8px rgba(0,0,0,0.3)"

            }),
            dcc.Download(id="download-shp"),
            create_dropdown(pollutants, show_all=False), # dropdown for pollutant selection
            dcc.DatePickerRange( # date picker for selecting the time range
            id="date-picker-range",
            min_date_allowed=datetime(2024, 1, 1), # default min date
            max_date_allowed=datetime(2025, 1, 1), # default max date
            start_date_placeholder_text="Start date",
            end_date_placeholder_text="End date",
            calendar_orientation='vertical',
            style={
                "position": "absolute",
                "top": "10px",
                "left": "100px",
                "zIndex": 800,
                "marginBottom": "20px",
                "backgroundColor": "white",
                "display": "flex", 
                "borderRadius": "8px",
                "boxShadow": "0 2px 8px rgba(0,0,0,0.3)",
                "marginTop": "10px",
                "cursor": "pointer",
            }
        ),
        ], style={"position": "relative"}),
        
        # legend for the map
        html.Div( id="map-legend",# legend container
                style={ # legend style
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
                "display": "none"               
                },
        )
    ], style={ # map container style
        "position": "relative",
        "borderRadius": "15px",
        "overflow": "hidden",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.2)",
        "marginBottom": "30px"
    }),
    html.Div([  # histogram container
        
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

    # Map of province names to their sigla (abbreviations in database, Extent in the shapefile)
    nome_to_sigla = { 
        "Milano": "MI", "Bergamo": "BG", "Brescia": "BS",
        "Como": "CO", "Cremona": "CR", "Lecco": "LC",
        "Lodi": "LO", "Mantua": "MN", "Monza and Brianza": "MB",
        "Pavia": "PV", "Sondrio": "SO", "Varese": "VA"
    }
    province["sigla"] = province["NAME_2"].map(nome_to_sigla) 
    # makes sure the province names match the ones in the database and join with the pollutant data
    gdf = province.merge(df_pollutant, left_on="sigla", right_on="provincia", how="left")
    # calculating the max and min values for the color scale 
    min_val = gdf["mean"].min()
    max_val = gdf["mean"].max()

    if pd.isna(min_val) or pd.isna(max_val):
        return []
    else:
    # Function to get the color based on the value
        def get_color(val):
            if pd.isna(val):
                return "#cccccc"  # grey for missing data
            if max_val - min_val < 1e-6: # if all values are the same, set a neutral color
                norm = 0.5
            else:
                norm = (val - min_val) / (max_val - min_val) # normalize the value between 0 and 1
            # color scale from green (low pollution) to yellow (medium pollution) to red (high pollution)
            if norm < 0.5:
                # from green to yellow
                r = int(255 * norm * 2)
                g = 255
                b = 0
            else:
                # from yellow to red
                r = 255
                g = int(255 * (1 - norm) * 2)
                b = 0
            # return the color in hex format
            return f"#{r:02x}{g:02x}{b:02x}"

        # Create legend values from min to max, divided into 4 intervals
        legend_values = [min_val + i * (max_val - min_val) / 4 for i in range(5)]
        # Add the title of the legend
        legend_elements = [html.P("Pollution Level", style={"margin": "0 0 10px 0", "fontWeight": "bold"})] 
        # Create ranges for the legend
        legend_ranges = [(legend_values[i], legend_values[i + 1]) for i in range(len(legend_values) - 1)]
        # Create colors for the legend based on the ranges
        legend_colors = [get_color((r[0] + r[1]) / 2) for r in legend_ranges]
        
        # Add legend elements with colors and ranges
        for (min_val, max_val), color in zip(legend_ranges, legend_colors):
            legend_elements.append(
                html.Div([ # legend internal layout
                    html.Div(style={
                        "width": "20px",
                        "height": "15px",
                        "backgroundColor": color,
                        "border": "1px solid black",
                        "marginRight": "8px",
                        "display": "inline-block"
                    }),
                    html.Span(f"{min_val:.1f} - {max_val:.1f}", style={"verticalAlign": "top"})
                ], style={"display": "flex", "alignItems": "center", "margin": "3px 0"})
            )
        # Add "No data"
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

    # Function to get the color for each province based on the mean value
    def get_color_discrete(val, legend_ranges, legend_colors):
        if pd.isna(val):
            return "#cccccc"  # no data
        for (min_r, max_r), color in zip(legend_ranges, legend_colors): 
            if min_r <= val <= max_r:
                return color
        # Se valore fuori range massimo, assegna colore ultimo intervallo
        return legend_colors[-1]

    # Apply the color function to each province based on the mean value
    gdf["color"] = [get_color_discrete(val, legend_ranges, legend_colors) for val in gdf["mean"]]
    # Create a tooltip with the province name and mean value, visible on hover
    gdf["tooltip"] = gdf["NAME_2"] + ": " + gdf["mean"].round(2).astype(str)

    # Create a list of children for the LayerGroup, list of polygons for each province
    children = []
    # Add polygons for each province
    for _, row in gdf.iterrows():
        # get the geometry of the province
        geom = row["geometry"]
        if geom.geom_type == 'Polygon':
            coords = [[[lat, lon] for lon, lat in geom.exterior.coords]] 
        elif geom.geom_type == 'MultiPolygon':
            coords = []
            for poly in geom.geoms:
                coords.append([[lat, lon] for lon, lat in poly.exterior.coords])
        
        # Set the fill color and tooltip text based on the mean value
        if pd.isna(row["mean"]):
            fill_color = "#cccccc"  # grey for missing data
            tooltip_text = f"{row['NAME_2']}: No data"
        else:
            fill_color = row["color"]
            tooltip_text = f"{row['NAME_2']}: {row['mean']:.2f}"
        
        # Create the polygon with the coordinates, fill color and tooltip
        polygon = dl.Polygon(
            id=f"poly-{uuid4()}", # unique id for each polygon
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
        # add the polygon to the list of children
        children.append(polygon)
    # return a LayerGroup with the list of polygons and the legend 
    return dl.FeatureGroup(children=children), legend_elements, gdf


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
                )
                fig.update_layout( # update the layout of the figure
                    xaxis_title="Province",
                    yaxis_title=f"Average {selected_pollutant} ({unit})",
                    title_x=0.5,
                    title={
                    'text': fig.layout.title.text,  # mantiene il testo attuale del titolo
                    'font': {'size': 24, 'family': 'Arial', 'color': 'black', 'weight': 'bold'}}
                )
                print("Updating map layer with", len(layer.children), "polygons")
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
        print(f"Error in the shapefile download: {e}")
        return dash.no_update


import dash
from dash import html, dcc, Output, Input
import pandas as pd
import plotly.graph_objs as go
import psycopg2
import dash_table
import geopandas as gpd
from shapely.geometry import Point

# --- Database Connection ---
def connect_to_postgres():
    return psycopg2.connect(
        host="localhost",
        database="lombardia_air_quality",
        user="airdata_user",
        password="user"
    )

# --- Fetch Province List ---
def get_provinces():
    conn = connect_to_postgres()
    df = pd.read_sql("SELECT DISTINCT provincia FROM station_data ORDER BY provincia", conn)
    conn.close()
    return df["provincia"].dropna().tolist()

# --- NOx Pollutant Categories ---
def get_nox_categories():
    return ["NO", "NO2", "NOx", "NO3"]

# --- Smoothing Options ---
def get_smoothing_options():
    return [
        {"label": "Raw Data", "value": "raw"},
        {"label": "Smoothed (7-day average)", "value": "smoothed"}
    ]

# --- Half-Year Options ---
def get_half_year_options():
    return [
        {"label": "First Half (Jan - Jun)", "value": "first"},
        {"label": "Second Half (Jul - Dec)", "value": "second"},
        {"label": "Full Year", "value": "full"}
    ]

# --- Fetch Data ---
def fetch_nox_data(province, pollutant, half):
    conn = connect_to_postgres()
    query = """
        SELECT s.data, s.valore, st.lon, st.lat
        FROM sensor_data s
        JOIN station_data st ON s.idstazione = st.idstazione
        WHERE st.provincia = %s AND s.nometiposensore = %s
              AND EXTRACT(YEAR FROM s.data) = 2024 AND s.stato = 'V'
    """
    df = pd.read_sql(query, conn, params=(province, pollutant))
    conn.close()

    df["data"] = pd.to_datetime(df["data"])
    df["valore"] = pd.to_numeric(df["valore"], errors="coerce")
    df = df.dropna()
    df.sort_values("data", inplace=True)
    df["smoothed"] = df["valore"].rolling(window=7, min_periods=1).mean()

    if half == "first":
        df = df[df["data"].dt.month <= 6]
    elif half == "second":
        df = df[df["data"].dt.month > 6]

    return df

# --- Initialize Dash App ---
app = dash.Dash(__name__)
app.title = "Lombardy NOx Air Quality Dashboard"

# --- App Layout ---
app.layout = html.Div(style={
    "backgroundColor": "#f4f6f9",
    "padding": "30px"
}, children=[
    html.Div(style={
        "backgroundColor": "white",
        "padding": "30px",
        "borderRadius": "10px",
        "boxShadow": "0px 4px 12px rgba(0,0,0,0.1)"
    }, children=[
        html.H2("\U0001F30D NOx Air Quality Monitoring in Lombardy", style={"textAlign": "center", "color": "#34495e"}),

        html.Div([
            html.Div([
                html.Label("\U0001F3E8 Select Province", style={"fontWeight": "bold"}),
                dcc.Dropdown(
                    id="province-dropdown",
                    options=[{"label": p, "value": p} for p in get_provinces()],
                    value="Milano",
                    clearable=False
                )
            ], style={"width": "24%", "display": "inline-block", "padding": 10}),

            html.Div([
                html.Label("\U0001F9EA Select NOx Category", style={"fontWeight": "bold"}),
                dcc.Dropdown(
                    id="pollutant-dropdown",
                    options=[{"label": p, "value": p} for p in get_nox_categories()],
                    value="NO2",
                    clearable=False
                )
            ], style={"width": "24%", "display": "inline-block", "padding": 10}),

            html.Div([
                html.Label("\U0001F527 Data Mode", style={"fontWeight": "bold"}),
                dcc.Dropdown(
                    id="smoothing-dropdown",
                    options=get_smoothing_options(),
                    value="raw",
                    clearable=False
                )
            ], style={"width": "24%", "display": "inline-block", "padding": 10}),

            html.Div([
                html.Label("\u23F0 Time Period", style={"fontWeight": "bold"}),
                dcc.Dropdown(
                    id="half-year-dropdown",
                    options=get_half_year_options(),
                    value="full",
                    clearable=False
                )
            ], style={"width": "24%", "display": "inline-block", "padding": 10})
        ]),

        dcc.Graph(id="nox-time-series"),

        html.Hr(),

        html.H4("\U0001F4C8 Tabular View of Data", style={"marginTop": 30, "color": "#34495e"}),
        dash_table.DataTable(
            id="data-table",
            columns=[
                {"name": "Date", "id": "data"},
                {"name": "Value (μg/m³g/m\xb3)", "id": "valore"}
            ],
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "center", "padding": "5px"},
            style_header={"backgroundColor": "#f9fafb", "fontWeight": "bold"}
        )
    ])
])

# --- Callback to Update Graph and Table ---
@app.callback(
    [Output("nox-time-series", "figure"),
     Output("data-table", "data")],
    [Input("province-dropdown", "value"),
     Input("pollutant-dropdown", "value"),
     Input("smoothing-dropdown", "value"),
     Input("half-year-dropdown", "value")]
)
def update_dashboard(province, pollutant, mode, half):
    df = fetch_nox_data(province, pollutant, half)

    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data available", x=0.5, y=0.5, showarrow=False)
        return fig, []

    y_data = df["valore"] if mode == "raw" else df["smoothed"]

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
        yaxis_title="Concentration (μg/m³g/m\xb3)",
        template="plotly_white",
        hovermode="x unified",
        margin=dict(l=30, r=30, t=60, b=30)
    )

    table_data = df[["data", "valore"]].round(2).to_dict("records")
    return fig, table_data

# --- Run the Server ---
if __name__ == '__main__':
    app.run_server(debug=True)

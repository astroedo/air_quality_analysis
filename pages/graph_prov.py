# Importazioni necessarie
import dash
from dash import html, dcc, Output, Input, callback
import plotly.express as px
import pandas as pd
import requests

# Registra pagina
dash.register_page(__name__, path="/trendprov", name="Trends")

from components.fetch_pollutant import fetch_pollutant
df_all = fetch_pollutant()

pollutants = sorted(df_all["nometiposensore"].dropna().unique()) if not df_all.empty else []
provinces = sorted(df_all["provincia"].dropna().unique()) if not df_all.empty else []

def fetch_sensor_data_api_by_province(provincia, pollutant, datainizio=None, datafine=None):
    url = "http://localhost:5000/api/measurements_by_province"
    params = {"provincia": provincia, "nometiposensore": pollutant}
    if datainizio: params["datainizio"] = datainizio
    if datafine: params["datafine"] = datafine

    try:
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        df = pd.DataFrame(resp.json())
        if 'data' in df:
            df['data'] = pd.to_datetime(df['data'])
        return df
    except Exception as e:
        print("API error:", e)
        return pd.DataFrame()

layout = html.Div([
    html.H2("📈 Air Quality Daily Averages by Province"),
    html.Div([
        html.Div([
            html.Label("🔬 Pollutant"),
            dcc.Dropdown(
                id="pollutant-dropdown",
                options=[{"label": p, "value": p} for p in pollutants],
                value=pollutants[0] if pollutants else None,
                clearable=False
            )
        ], style={"width":"45%", "marginRight":"5%"}),
        html.Div([
            html.Label("🏙️ Province"),
            dcc.Dropdown(
                id="province-dropdown",
                options=[{"label": p, "value": p} for p in provinces],
                value=provinces[0] if provinces else None,
                clearable=False
            )
        ], style={"width":"45%"})
    ], style={"display":"flex", "marginBottom":"20px"}),
    dcc.Graph(id="trend-graph")
], style={
    "paddingLeft": "20px",
    "paddingRight": "20px",
    "maxWidth": "1200px",
    "margin": "auto"
})

@callback(
    Output("trend-graph", "figure"),
    [Input("pollutant-dropdown", "value"),
     Input("province-dropdown", "value")]
)
def update_graph(pollutant, province):
    if not pollutant or not province:
        return px.line(title="Select both pollutant and province")

    df = fetch_sensor_data_api_by_province(provincia=province, pollutant=pollutant)
    if df.empty or 'data' not in df:
        fig = px.line()
        fig.add_annotation(text="No data", x=0.5, y=0.5, showarrow=False, xref="paper", yref="paper")
        return fig

    # Calcola media giornaliera con resample
    df = df.set_index('data').resample('D')['valore'].mean().dropna().reset_index()
    # :contentReference[oaicite:1]{index=1}

    if df.empty:
        fig = px.line()
        fig.add_annotation(text="No data after aggregation", x=0.5, y=0.5, showarrow=False, xref="paper", yref="paper")
        return fig

    fig = px.line(
        df,
        x="data", y="valore",
        title=f"Daily average of {pollutant} in {province}",
        labels={"data": "Date", "valore": f"{pollutant} (μg/m³)"}
    )
    fig.update_layout(xaxis=dict(rangeslider=dict(visible=True), type="date"))
    return fig

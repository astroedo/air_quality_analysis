# pages/home_page.py
"""
Home page with a welcome message, background image, and link to the map page.
"""

import dash
from dash import html, dcc

dash.register_page(__name__, path="/", name="Home")

layout = html.Div(
    style={
        "height": "100vh",
        "display": "flex",
        "flexDirection": "column",
        "justifyContent": "center",
        "alignItems": "center",
        "backgroundImage": "url('https://images.unsplash.com/photo-1506744038136-46273834b3fb')",
        "backgroundSize": "cover",
        "color": "white",
        "textAlign": "center",
        "padding": "0px"
    },
    children=[
        html.Img( src="/assets/logo.png", style = { "height" :"100px",  "width" : "100px", "marginRight": "0px",  "verticalAlign": "middle" }  ),
        html.H1("Welcome to GeoAir", style={"fontSize": "4rem", "marginBottom": "20px"}),
        html.P("Monitor air quality across Lombardia with real-time data", style={"fontSize": "1.5rem"}),
        dcc.Link(
            "Go to Map ➔",
            href="/map",
            style={
                "marginTop": "30px",
                "fontSize": "1.5rem",
                "color": "#fff",
                "textDecoration": "underline",
                "cursor": "pointer"
            }
        )
    ]
)

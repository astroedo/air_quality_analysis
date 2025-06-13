import dash
from dash import html, dcc, page_container
from functions.logger import setup_logging

setup_logging()

app = dash.Dash(__name__, use_pages=True, suppress_callback_exceptions=True)
server = app.server

app.layout = html.Div([

    # Navbar
    html.Div([
        # Logo and title
        dcc.Link(
            "GeoAir - Air Quality Analysis",
            href="/",
            style={
                "fontSize": "24px",
                "fontWeight": "bold",
                "color": "white",
                "padding": "10px 20px",
                "textDecoration": "none"  # remove underline
            }
        ),

        # Navigation links
        html.Div([
            dcc.Link("Home", href="/", style={
                "marginRight": "20px",
                "color": "white",
                "textDecoration": "none",
                "fontSize": "16px"
            }),
            dcc.Link("Map", href="/map", style={
                "color": "white",
                "textDecoration": "none",
                "fontSize": "16px"
            })
        ], style={"padding": "10px 20px"})
        
    ], style={
        "display": "flex",
        "justifyContent": "space-between",
        "alignItems": "center",
        "backgroundColor": "rgb(19 129 159)",
        "position": "fixed",
        "width": "100%",
        "height": "60px",
        "top": 0,
        "zIndex": 1001
    }),

    # Page container for the content
    html.Div(page_container, style={"paddingTop": "60px"})
])


if __name__ == "__main__":
    print("🚀 GeoAir in esecuzione su http://127.0.0.1:8000")
    app.run(debug=True, port=8000)

import dash
from dash import html, dcc, page_container
from components.logger import setup_logging
from dash import Input, Output, State, callback, no_update
setup_logging()

app = dash.Dash(__name__, use_pages=True, suppress_callback_exceptions=True)
server = app.server


app.layout = html.Div([

    dcc.Store(id="session", storage_type="session"),
    dcc.Location(id="logout-redirect"),
    # dcc.Location(id="url"),   Per abilitare i redirect #
    #
    # Navbar
    html.Div([
        # Logo and title
        dcc.Link([
            html.Div([
                html.Img(
                    src="/assets/logo.png",
                    style = {
                        "height" :"40px",
                        "width" : "40px",
                        "marginRight": "0px",
                        "verticalAlign": "middle"
                    }
                ),
                html.Span(
                    "GeoAir",
                    style={
                        "fontSize": "24px",
                        "fontWeight": "bold",
                        "color": "white",
                        "padding": "10px 20px",
                        "textDecoration": "none"  # remove underline
                    }
                )
            ], style = {
                "display": "flex",
                "alignItems": "center",
                "padding": "10px 20px"
            })
        ], 
        href="/",
        style = {
            "textDecoration": "none"
        }),

        # Navigation links
        html.Div([
            dcc.Link("Home", href="/", style={
                "marginRight": "20px",
                "color": "white",
                "textDecoration": "none",
                "fontSize": "16px"
            }),
            dcc.Link("Map", href="/map", style={
                "marginRight": "20px",
                "color": "white",
                "textDecoration": "none",
                "fontSize": "16px"
            }),
            dcc.Link("Trends", href="/trend", style = {
                "marginRight": "20px",
                "color": "white",
                "textDecoration": "none",
                "fontSize": "16px"
            }),
            dcc.Link("Login", href="/login", style={
                "marginRight": "20px",
                "color": "white",
                "textDecoration": "none",
                "fontSize": "16px"
            }),
            html.Button("Logout", id="logout-button", n_clicks=0, style={
            "backgroundColor": "transparent",
            "color": "white",
            "border": "none",
            "cursor": "pointer",
            "fontSize": "16px"
        })

        ], style={"padding": "10px 20px "})
        
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
    html.Div(page_container, style={
        "flex": "1",
        "paddingTop": "60px",  # fixed navbar height
        "overflow": "auto"     
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
],
style={
    "display": "flex",
    "flexDirection": "column",
    "minHeight": "100vh"   # altezza minima viewport
})

# Callback to handle logout
@callback(
    [Output("session", "data", allow_duplicate=True),
     Output("logout-redirect", "href")],
    Input("logout-button", "n_clicks"),
    prevent_initial_call=True
)
def logout(n_clicks):
    if n_clicks:
        return {}, "/"  # Clear session data and redirect to home page
    return no_update, no_update

# Callback to update the visibility of the logout button
@callback(
    Output("logout-button", "style"),
    Input("session", "data"),
)
def update_logout_button_visibility(session_data):
    if session_data and session_data.get("logged_in", False):
        return {
            "backgroundColor": "transparent",
            "color": "white",
            "border": "none",
            "cursor": "pointer",
            "fontSize": "16px",
            "display": "inline-block"
        }
    return {"display": "none"}

if __name__ == "__main__":
    print("🚀 GeoAir in esecuzione su http://127.0.0.1:8000")
    app.run(debug=True, port=8000)

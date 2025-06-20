import dash
from dash import html, dcc, Input, Output, State, callback
import requests

dash.register_page(__name__, path="/login", name="Login")

layout = html.Div([

    html.Div([
        html.H2("Login to Your Account", style={
            "textAlign": "center",
            "marginBottom": "30px",
            "color": "#136E87"
        }),

        dcc.Input(
            id="login-username",
            type="text",
            placeholder="Username",
            style={
                "padding": "10px",
                "width": "100%",
                "marginBottom": "15px",
                "border": "1px solid #ccc",
                "borderRadius": "5px",
                "boxSizing": "border-box"
            }
        ),

        dcc.Input(
            id="login-password",
            type="password",
            placeholder="Password",
            style={
                "padding": "10px",
                "width": "100%",
                "marginBottom": "20px",
                "border": "1px solid #ccc",
                "borderRadius": "5px",
                "boxSizing": "border-box"
            }
        ),

        html.Button("Login", id="login-button", style={
            "width": "100%",
            "padding": "12px",
            "backgroundColor": "#136E87",
            "color": "white",
            "border": "none",
            "borderRadius": "5px",
            "cursor": "pointer",
            "boxSizing": "border-box"
        }),

        # Logout button sempre visibile e con stesso stile
        html.Button("Logout", id="logout-button", style={
            "width": "100%",
            "padding": "12px",
            "backgroundColor": "#d9534f",  # rosso
            "color": "white",
            "border": "none",
            "borderRadius": "5px",
            "cursor": "pointer",
            "boxSizing": "border-box",
            "marginTop": "10px"
        }),

        html.Div(id="login-message", style={
            "marginTop": "20px",
            "textAlign": "center",
            "color": "red"
        }),

    ], style={
        "maxWidth": "400px",
        "margin": "80px auto",
        "padding": "40px",
        "border": "1px solid #eee",
        "borderRadius": "10px",
        "boxShadow": "0 4px 12px rgba(0,0,0,0.1)",
        "boxSizing": "border-box"
    })
])


@callback(
    Output("login-message", "children"),
    Output("jwt-token", "data"),
    Input("login-button", "n_clicks"),
    Input("logout-button", "n_clicks"),
    State("login-username", "value"),
    State("login-password", "value"),
    State("jwt-token", "data"),
    prevent_initial_call=True
)
def handle_login_logout(login_clicks, logout_clicks, username, password, token):
    ctx = dash.callback_context

    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Se cliccato logout
    if triggered_id == "logout-button":
        return "Logged out successfully.", None

    # Se cliccato login
    if triggered_id == "login-button":
        if not username or not password:
            return "Please enter both username and password.", token

        try:
            url = "http://localhost:5000/api/login"
            response = requests.post(url, json={"username": username, "password": password})

            if response.status_code == 200:
                new_token = response.json().get("token")
                return html.Span("Login successful.", style={"color": "green"}), new_token

            if response.status_code in (400, 401, 409, 500):
                body = response.json()
                msg = body.get("message") or body.get("error") or "Unknown error"
                return f"Error ({response.status_code}): {msg}", None

            return f"Error ({response.status_code}): {response.text}", None

        except requests.exceptions.RequestException as e:
            return f"Connection error: {e}", None

    return dash.no_update

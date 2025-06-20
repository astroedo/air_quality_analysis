import dash
from dash import html, dcc, Input, Output, State, callback
import requests

dash.register_page(__name__, path="/register", name="Register")

layout = html.Div([
    html.Div([
        html.H2("Create a New Account", style={
            "textAlign": "center",
            "marginBottom": "30px",
            "color": "#13819f"
        }),

        # Container for inputs and button, con larghezza fissa
        html.Div([
            dcc.Input(
                id="register-username",
                type="text",
                placeholder="Username",
                style={
                    "width": "100%",
                    "padding": "10px",
                    "fontSize": "16px",
                    "border": "1px solid #ccc",
                    "borderRadius": "5px",
                    "boxSizing": "border-box"  
                }
            ),
            dcc.Input(
                id="register-email",
                type="email",
                placeholder="Email",
                style={
                    "width": "100%",
                    "padding": "10px",
                    "fontSize": "16px",
                    "border": "1px solid #ccc",
                    "borderRadius": "5px",
                    "boxSizing": "border-box"  
                }
            ),
            dcc.Input(
                id="register-password",
                type="password",
                placeholder="Password",
                style={
                    "width": "100%",
                    "padding": "10px",
                    "fontSize": "16px",
                    "border": "1px solid #ccc",
                    "borderRadius": "5px",
                    "boxSizing": "border-box"  
                }
            ),
            html.Button(
                "Register",
                id="register-button",
                style={
                    "width": "100%",
                    "padding": "12px",
                    "fontSize": "16px",
                    "backgroundColor": "#13819f",
                    "color": "white",
                    "border": "none",
                    "borderRadius": "5px",
                    "cursor": "pointer",
                    "marginTop": "10px"
                }
            )
        ], style={
            "display": "flex",
            "flexDirection": "column",
            "gap": "15px",
            "width": "100%"
        }),

        html.Div(id="register-message", style={
            "marginTop": "20px",
            "textAlign": "center",
            "color": "red"
        }),
    ], style={
        "maxWidth": "400px",
        "margin": "80px auto",
        "padding": "20px",
        "borderRadius": "8px",
        "boxShadow": "0 4px 12px rgba(0,0,0,0.1)",
        "backgroundColor": "white"
    })
])

@callback(
    Output("register-message", "children"),
    Input("register-button", "n_clicks"),
    State("register-username", "value"),
    State("register-email", "value"),
    State("register-password", "value"),
    prevent_initial_call=True
)
def handle_registration(n_clicks, username, email, password):
    if not username or not email or not password:
        return "Please fill in all fields."

    try:
        response = requests.post("http://localhost:5000/api/register", json={
            "username": username,
            "email": email,
            "password": password
        })

        if response.status_code == 201:
            return html.Span("Registration successful. You can now log in.", style={"color": "green"})
        elif response.status_code == 409:
            return "Username or email already exists."
        else:
            msg = response.json().get("message", "Unknown error")
            return f"Error: {msg}"

    except Exception as e:
        return f"Server connection error: {str(e)}"

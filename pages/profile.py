import dash
from dash import html, dcc, Input, Output, callback
import requests

dash.register_page(__name__, path="/profile", name="Profile")

layout = html.Div([
    html.H2("User Profile", style={
        "textAlign": "center",
        "marginBottom": "30px",
        "color": "#13819f",
        "fontWeight": "bold"
    }),

    dcc.Location(id='url', refresh=True),
    
    html.Div(id="profile-content", style={
        "maxWidth": "500px",
        "margin": "auto",
        "padding": "30px",
        "borderRadius": "10px",
        "boxShadow": "0 4px 16px rgba(0,0,0,0.1)",
        "backgroundColor": "white",
        "textAlign": "left",
        "fontSize": "16px",
        "color": "#333"
    }),

    # 🔗 Link sempre visibile per andare alla pagina login
    html.Div([
        dcc.Link("Go to Login", href="/login", style={
            "marginTop": "30px",
            "display": "inline-block",
            "padding": "10px 20px",
            "backgroundColor": "#13819f",
            "color": "white",
            "borderRadius": "5px",
            "textDecoration": "none",
            "fontWeight": "bold"
        })
    ], style={"textAlign": "center", "marginTop": "20px"})
])


@callback(
    Output("profile-content", "children"),
    Input("jwt-token", "data")
)
def load_profile(token):
    if not token:
        return html.Div("You are not logged in.", style={
            "textAlign": "center",
            "color": "red"
        })

    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get("http://localhost:5000/api/profile", headers=headers)

        if response.status_code == 200:
            user = response.json()
            created_at = user.get("created_at", "")[:10]
            return html.Div([
                html.P(f"👤 Username: {user.get('username', '')}"),
                html.P(f"📧 Email: {user.get('email', '')}"),
                html.P(f"🔑 Type: {user.get('type', '')}"),
                html.P(f"📅 Created at: {created_at}")
            ])
        else:
            return html.Div("Failed to fetch profile data.", style={"textAlign": "center", "color": "red"})

    except Exception as e:
        return html.Div(f"Error: {str(e)}", style={"textAlign": "center", "color": "red"})

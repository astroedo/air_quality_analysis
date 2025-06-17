# pages/login_page.py

# package imports
import dash
from dash import html, dcc
from dash import Input, Output, State, callback
import requests

# Register the page with Dash
dash.register_page(__name__, path='/login', name='Login')
# Define the layout for the login page
layout = html.Div([
    html.H1("Login"),
    dcc.Input(placeholder='Username', type='text', id='username'),
    dcc.Input(placeholder='Password', type='password', id='password'),
    html.Button('Accedi', id='login-button', n_clicks=0),
    html.Div(id='login-output')
], style={
    'width': '300px',
    'margin': '100px auto',
    'display': 'flex',
    'flexDirection': 'column',
    'gap': '10px'
})

@dash.callback(
    Output('login-output', 'children'),
    Input('login-button', 'n_clicks'),
    State('username', 'value'),
    State('password', 'value'),
    prevent_initial_call=True
)

def handle_login(n_clicks, username, password):
    if n_clicks > 0:
        try:
            res = requests.post("http://localhost:8000/api/login", json={
                "username": username,
                "password": password
            })
            if res.status_code == 200:
                    return "Login successful!"
            else:
                return "Login failed"
        except Exception as e:
                return f"Connection error: {str(e)}"



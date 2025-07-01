# pages/login_page.py

import dash
from dash import html, dcc, ctx
from dash import Input, Output, State, callback, no_update
import requests

dash.register_page(__name__, path='/login', name='Login')

input_style = {
    'padding': '10px',
    'width': '100%',
    'borderRadius': '5px',
    'border': '1px solid #ccc',
    'boxSizing': 'border-box'
}

button_style = {
    'padding': '12px 20px',
    'width': '100%',
    'borderRadius': '8px',
    'border': 'none',
    'backgroundColor': '#007b8f',
    'color': 'white',
    'fontWeight': '600',
    'fontSize': '16px',
    'cursor': 'pointer',
    'boxShadow': '0 4px 8px rgba(0, 123, 143, 0.3)',
    'transition': 'background-color 0.3s ease, box-shadow 0.3s ease',
    'userSelect': 'none',
    'textAlign': 'center',
    'fontFamily': "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
}


field_group_style = {
    'display': 'flex',
    'flexDirection': 'column',
    'gap': '10px'
}

form_card_style = {
    'width': '300px',
    'margin': '100px auto',
    'display': 'flex',
    'flexDirection': 'column',
    'gap': '10px',
    'boxShadow': '0 0 10px rgba(0,0,0,0.1)',
    'padding': '20px',
    'borderRadius': '10px',
    'backgroundColor': '#ffffff',
    'boxSizing': 'border-box'
}

signup_style = {**field_group_style, 'display': 'block'}

layout = html.Div([
    dcc.Location(id="url"),
    html.H1("Login", id='page-title', style={'textAlign': 'center'}),

    html.Div([
        html.Div([
            dcc.Input(placeholder='Username', type='text', id='username',
                      style=input_style),
            dcc.Input(placeholder='Password', type='password', id='password',
                      style=input_style),
        ], id='login-fields', style=field_group_style),

        html.Div([
            dcc.Input(placeholder='Email', type='email', id='email',
                      style=input_style),
            dcc.Input(placeholder='Confirm Password', type='password', id='confirm-password',
                      style={**input_style, 'marginTop': '10px'}),
        ], id='signup-fields', style={'display': 'none'}),

        html.Button('Login', id='login-button', n_clicks=0, style=button_style),
        html.Button('Sign-in', id='signup-button', n_clicks=0,
                    style={'display': 'none'}),
        html.Button('Back to lognin', id='back-to-login', n_clicks=0,
                    style={'display': 'none'}),

        html.Div(id='login-output', style={'textAlign': 'center', 'color': 'red', 'marginTop': '10px'})
    ], style=form_card_style)
])

def default_login_return(login_output="", session_data=no_update):
    return (
        {'display': 'none'},  # signup-fields.style
        {'display': 'none'},  # signup-button.style
        {'display': 'none'},  # back-to-login.style
        {**button_style, 'display': 'block'}, # login-button.style
        "Login",              # page-title.children
        login_output,         # login-output.children
        session_data          # session.data
    )

@callback(
    [Output('signup-fields', 'style'),
     Output('signup-button', 'style'),
     Output('back-to-login', 'style'),
     Output('login-button', 'style'),
     Output('page-title', 'children'),
     Output('login-output', 'children', allow_duplicate=True),
     Output('session', 'data')],
    [Input('login-button', 'n_clicks'),
     Input('back-to-login', 'n_clicks')],
    [State('username', 'value'),
     State('password', 'value')],
    prevent_initial_call=True,
    allow_duplicate=True
)
def handle_login_and_show_signup(login_clicks, back_clicks, username, password):
    ctx = dash.callback_context
    if not ctx.triggered:
        return default_login_return()

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == 'back-to-login':
        return (
            {'display': 'none'},  # signup-fields
            {'display': 'none'},  # signup-button
            {'display': 'none'},  # back-to-login
            {**button_style, 'display': 'block'}, # login-button
            "Login",
            "",
            no_update
        )

    if trigger_id == 'login-button' and login_clicks > 0:
        if not username or not password:
            return default_login_return("Insert username e password")

        try:
            res = requests.post("http://localhost:5001/api/login", json={
                "username": username,
                "password": password
            })
            if res.status_code == 200:
                return (
                    {'display': 'none'},
                    {'display': 'none'},
                    {'display': 'none'},
                    {**button_style, 'display': 'block'},
                    "Login",
                    "Login successful!",
                    {"logged_in": True, "username": username}
                )
            elif res.status_code == 403:
                return default_login_return("Wrong password.")
            elif res.status_code == 401:
                return (
                    {'display': 'block'},   # signup-fields
                    {**button_style, 'display': 'block'},   # signup-button
                    {**button_style, 'display': 'block'},   # back-to-login
                    {'display': 'none'},    # login-button
                    "Registration",
                    "Username not found. Please register.",
                    no_update
                )
            else:
                return default_login_return(f"Errore: {res.status_code} - {res.text}")
        except requests.exceptions.RequestException as e:
            return default_login_return(f"Errore di connessione: {str(e)}")

    return default_login_return()

@callback(
    Output('login-output', 'children'),
    Input('signup-button', 'n_clicks'),
    State('username', 'value'),
    State('password', 'value'),
    State('email', 'value'),
    State('confirm-password', 'value'),
    prevent_initial_call=True
)
def handle_signin(n_clicks, username, password, email, confirm_password):
    if n_clicks > 0:
        if not all([username, password, email, confirm_password]):
            return "Please, fill all the fields."
        if password != confirm_password:
            return "The passwords are different."
        try:
            res = requests.post("http://localhost:5001/api/signin", json={
                "username": username,
                "password": password,
                "email": email
            })
            if res.status_code in (200, 201):
                return "Registration completed! Now you can login."
            else:
                return f"Error in registration: {res.status_code} - {res.text}"
        except requests.exceptions.RequestException as e:
            return f"Connection error: {str(e)}"
    return ""

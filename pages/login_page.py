# pages/login_page.py

# --- Package imports ---
import dash
from dash import html, dcc, Input, Output, State, callback
from components.api_login import api_login
from components.api_signin import api_signin

# --- Register the page ---
dash.register_page(__name__, path='/login', name='Login')

# --- Styles ---
input_style = {
    'padding': '10px', 'width': '100%', 'borderRadius': '5px',
    'border': '1px solid #ccc', 'boxSizing': 'border-box'
}

button_base_style = {
    'padding': '10px', 'width': '100%', 'borderRadius': '5px',
    'border': 'none', 'backgroundColor': '#007b8f',
    'color': 'white', 'fontWeight': 'bold', 'cursor': 'pointer',
    'boxSizing': 'border-box'
}

field_group_style = {'display': 'flex', 'flexDirection': 'column', 'gap': '10px'}

form_card_style = {
    'width': '300px', 'margin': '100px auto', 'display': 'flex',
    'flexDirection': 'column', 'gap': '10px', 'boxShadow': '0 0 10px rgba(0,0,0,0.1)',
    'padding': '20px', 'borderRadius': '10px', 'backgroundColor': '#ffffff',
    'boxSizing': 'border-box'
}

# --- Utility functions ---
def show_button():
    return {**button_base_style, 'display': 'block'}

def hide_button():
    return {**button_base_style, 'display': 'none'}

def get_login_response_ui(result):
    """Return UI outputs based on the API login response."""
    status = result["status"]
    if status == "missing":
        return [hide_button()] * 3 + [show_button()] + ["Login", "Please enter username and password."]
    if status == 200:
        return [hide_button()] * 3 + [show_button()] + ["Login", "Login successful!"]
    if status == 403:
        return [hide_button()] * 3 + [show_button()] + ["Login", "Incorrect password."]
    if status == 401:
        return (
            {'display': 'block'}, show_button(), show_button(), hide_button(),
            "Sign up", "Username not found. Please register with all your data."
        )
    if status == "error":
        return [hide_button()] * 3 + [show_button()] + ["Login", f"Connection error: {result['text']}"]
    return [hide_button()] * 3 + [show_button()] + ["Login", "Unexpected response."]

# --- Layout ---
layout = html.Div([
    html.H1("Login", id='page-title', style={'textAlign': 'center'}),

    html.Div([
        html.Div([
            dcc.Input(id='username', placeholder='Username', type='text', style=input_style),
            dcc.Input(id='password', placeholder='Password', type='password', style=input_style),
        ], id='login-fields', style=field_group_style),

        html.Div([
            dcc.Input(id='email', placeholder='Email', type='email', style=input_style),
            dcc.Input(id='confirm-password', placeholder='Confirm Password', type='password',
                      style={**input_style, 'marginTop': '10px'}),
        ], id='signup-fields', style={'display': 'none'}),

        html.Button('Login', id='login-button', n_clicks=0, style=show_button()),
        html.Button('Sign-in', id='signup-button', n_clicks=0, style=hide_button()),
        html.Button('Back to login', id='back-to-login', n_clicks=0, style=hide_button()),

        html.Div(id='login-output', style={'textAlign': 'center', 'color': 'red', 'marginTop': '10px'})
    ], style=form_card_style)
])

# --- Callbacks ---

@callback(
    [Output('signup-fields', 'style'),
     Output('signup-button', 'style'),
     Output('back-to-login', 'style'),
     Output('login-button', 'style'),
     Output('page-title', 'children'),
     Output('login-output', 'children', allow_duplicate=True)],
    [Input('login-button', 'n_clicks'),
     Input('back-to-login', 'n_clicks')],
    [State('username', 'value'),
     State('password', 'value')],
    prevent_initial_call=True
)
def handle_login_and_show_signup(login_clicks, back_clicks, username, password):
    ctx = dash.callback_context
    if not ctx.triggered:
        return [hide_button()] * 3 + [show_button()] + ["Login", ""]

    trigger = ctx.triggered[0]['prop_id'].split('.')[0]
    if trigger == 'back-to-login':
        return [hide_button()] * 3 + [show_button()] + ["Login", ""]
    if trigger == 'login-button' and login_clicks > 0:
        result = api_login(username, password)
        return get_login_response_ui(result)
    return [hide_button()] * 3 + [show_button()] + ["Login", ""]

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
        return api_signin(username, password, email, confirm_password)
    return ""
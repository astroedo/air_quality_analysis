# pages/login_page.py

import dash
from dash import html, dcc, ctx, clientside_callback, ClientsideFunction
from dash import Input, Output, State, callback, no_update
import requests

dash.register_page(__name__, path='/login', name='Login')
# style definitions for the login page components
input_style = { # Style for input fields
    'padding': '10px',
    'width': '100%',
    'borderRadius': '5px',
    'border': '1px solid #ccc',
    'boxSizing': 'border-box'
}

button_style = { # Style for buttons
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

field_group_style = { # Style for the group of input fields
    'display': 'flex',
    'flexDirection': 'column',
    'gap': '10px'
}

form_card_style = { # Style for the form card container
    'width': '300px',
    'margin': '50px auto',
    'display': 'flex',
    'flexDirection': 'column',
    'gap': '10px',
    'boxShadow': '0 0 10px rgba(0,0,0,0.1)',
    'padding': '20px',
    'borderRadius': '10px',
    'backgroundColor': '#ffffff',
    'boxSizing': 'border-box'
}

layout = html.Div([
    # Store to manage page state
    dcc.Store(id='login-page-store', data={'mode': 'login'}),
    
    html.H1("Login", id='login-page-title', style={'textAlign': 'center'}), # Title of the page
    html.Div(id='login-user-info', style={'textAlign': 'center', 'marginBottom': '20px'}), # User info display

    html.Div([ # Login form container
        html.Div([
            dcc.Input(placeholder='Username', type='text', id='login-username',
                      style=input_style),
            dcc.Input(placeholder='Password', type='password', id='login-password',
                      style=input_style),
        ], id='login-fields', style=field_group_style),

        html.Div([
            dcc.Input(placeholder='Email', type='email', id='login-email',
                      style=input_style),
            dcc.Input(placeholder='Confirm Password', type='password', id='login-confirm-password',
                      style={**input_style, 'marginTop': '10px'}),
        ], id='signup-fields', style={'display': 'none'}),

        html.Button('Login', id='login-button', n_clicks=0, style=button_style),
        html.Button('Sign-in', id='signup-button', n_clicks=0,
                    style={'display': 'none'}),
        html.Button('Back to login', id='back-to-login', n_clicks=0,
                    style={'display': 'none'}),
    ], id='login-form-container', style=form_card_style),
    
    # Sposto login-output fuori dal form container
    html.Div(id='login-output', style={'textAlign': 'center', 'color': 'red', 'marginTop': '10px'})
])

# Callback per gestire il cambio modalità (login/signup)
@callback(
    [Output('signup-fields', 'style'),
     Output('signup-button', 'style'),
     Output('back-to-login', 'style'),
     Output('login-button', 'style'),
     Output('login-page-title', 'children'),
     Output('login-page-store', 'data')],
    [Input('back-to-login', 'n_clicks'),
     Input('login-page-store', 'data')],
    prevent_initial_call='initial_duplicate'
)
def toggle_login_signup(back_clicks, store_data):
    ctx = dash.callback_context
    
    # default mode is 'login'
    if not ctx.triggered or not back_clicks or ctx.triggered[0]['prop_id'] == 'back-to-login.n_clicks':
        return (
            {'display': 'none'},  # signup-fields
            {'display': 'none'},  # signup-button
            {'display': 'none'},  # back-to-login
            {**button_style, 'display': 'block'}, # login-button
            "Login",
            {'mode': 'login'}
        )

    return dash.no_update

# # Callback to check if the user is already logged in when the page loads
@callback(
    [Output('login-form-container', 'style'),
     Output('login-page-title', 'children', allow_duplicate=True),
     Output('login-output', 'children', allow_duplicate=True),
     Output('login-output', 'style', allow_duplicate=True)],
    Input('session', 'data'),
    prevent_initial_call='initial_duplicate',
    allow_duplicate=True
)
def check_login_status(session_data):
    if session_data and session_data.get("logged_in", False):
        username = session_data.get("username", "unknown user")
        return (
            {'display': 'none'},  # Nasconde tutto il form
            "Welcome to GeoAir!", # title of the page
            f"You are logged in as {username}. Please, logout to switch user.", # output message
            {'color': 'black', 'textAlign': 'center', 'marginTop': '20px', 'fontWeight': 'bold'}  # style for the output message 
        )
    else:
        return (
            form_card_style,  # Mostra il form
            "Login",
            "",
            no_update
        )

# Callback per gestire il login
@callback(
    [Output('signup-fields', 'style', allow_duplicate=True),
     Output('signup-button', 'style', allow_duplicate=True),
     Output('back-to-login', 'style', allow_duplicate=True),
     Output('login-button', 'style', allow_duplicate=True),
     Output('login-page-title', 'children', allow_duplicate=True),
     Output('login-output', 'children', allow_duplicate=True),
     Output('login-output', 'style', allow_duplicate=True),
     Output('session', 'data', allow_duplicate=True)],
    Input('login-button', 'n_clicks'),
    [State('login-username', 'value'),
     State('login-password', 'value'),
     State('session', 'data')],
    prevent_initial_call=True,
    allow_duplicate=True
)
def handle_login(login_clicks, username, password, session_data):
    # If the button is not clicked, do nothing
    if not login_clicks or login_clicks == 0:
        return dash.no_update
    # If there is no username or password, return an error message
    if not username or not password:
        return (
            dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
            "Insert username and password",
            {'color': 'red', 'textAlign': 'center', 'marginTop': '10px', 'fontWeight': 'bold'},
            dash.no_update
        )
    try: # make the request to the backend
        res = requests.post("http://localhost:5001/api/login", json={
            "username": username,
            "password": password
        })
        if res.status_code == 200: # Login successful
            return (
                {'display': 'none'}, {'display': 'none'}, {'display': 'none'},
                {**button_style, 'display': 'block'},
                f"Welcome, {username}!",
                "Login successful!",
                {'color': "#0ea80e", 'textAlign': 'center', 'marginTop': '10px', 'fontWeight': 'bold'},
                {"logged_in": True, "username": username}
            )
        elif res.status_code == 403: # Wrong password
            return (
                dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                "Wrong password.",
                {'color': 'red', 'textAlign': 'center', 'marginTop': '10px', 'fontWeight': 'bold'},
                dash.no_update
            )
        elif res.status_code == 401: # Username not found
            return (
                {'display': 'block'},   # signup-fields shown
                {**button_style, 'display': 'block'},   # signup-button
                {**button_style, 'display': 'block'},   # back-to-login
                {'display': 'none'},    # login-button
                "Registration",
                "Username not found. Please register.",
                {'color': 'red', 'textAlign': 'center', 'marginTop': '10px', 'fontWeight': 'bold'},
                dash.no_update
            )
        else: # Other errors
            return ( 
                dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                f"Error: {res.status_code} - {res.text}",
                {'color': 'red', 'textAlign': 'center', 'marginTop': '10px', 'fontWeight': 'bold'},
                dash.no_update
            )
    except requests.exceptions.RequestException as e: # Handle connection errors
        return (
            dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
            f"Connection error: {str(e)}",
            {'color': 'red', 'textAlign': 'center', 'marginTop': '10px', 'fontWeight': 'bold'},
            dash.no_update
        )

# Callback to handle the signup
@callback(
    [Output('login-output', 'children', allow_duplicate=True),
     Output('login-output', 'style', allow_duplicate=True)],
    Input('signup-button', 'n_clicks'),
    [State('login-username', 'value'),
     State('login-password', 'value'),
     State('login-email', 'value'),
     State('login-confirm-password', 'value')],
    prevent_initial_call=True,
    allow_duplicate=True
)
def handle_signin(n_clicks, username, password, email, confirm_password):
    if not n_clicks or n_clicks == 0: # If the button is not clicked, do nothing
        return dash.no_update
        
    if not all([username, password, email, confirm_password]): # Check if all fields are filled
        return ("Please, fill all the fields.", 
                {'color': 'red', 'textAlign': 'center', 'marginTop': '10px', 'fontWeight': 'bold'})
    if password != confirm_password: # Check if passwords match
        return ("The passwords are different.", 
                {'color': 'red', 'textAlign': 'center', 'marginTop': '10px', 'fontWeight': 'bold'})
    try: 
        res = requests.post("http://localhost:5001/api/signin", json={
            "username": username,
            "password": password,
            "email": email
        })
        if res.status_code in (200, 201): # Registration successful
            return ("Registration completed! Now you can login.", 
                    {'color': '#0ea80e', 'textAlign': 'center', 'marginTop': '10px', 'fontWeight': 'bold'})
        else: # Handle errors
            return (f"Error in registration: {res.status_code} - {res.text}", 
                    {'color': 'red', 'textAlign': 'center', 'marginTop': '10px', 'fontWeight': 'bold'})
    except requests.exceptions.RequestException as e: # Handle connection errors
        return (f"Connection error: {str(e)}", 
                {'color': 'red', 'textAlign': 'center', 'marginTop': '10px', 'fontWeight': 'bold'})
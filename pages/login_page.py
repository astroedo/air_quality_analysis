# pages/login_page.py

# package imports
import dash
from dash import html, dcc, ctx
from dash import Input, Output, State, callback, no_update
import requests
# Register the page with Dash
dash.register_page(__name__, path='/login', name='Login')

# style definitions
input_style = {
    'padding': '10px',
    'width': '100%',
    'borderRadius': '5px',
    'border': '1px solid #ccc',
    'boxSizing': 'border-box'
}

button_style = {
    'padding': '10px',
    'width': '100%',
    'borderRadius': '5px',
    'border': 'none',
    'backgroundColor': '#007b8f',
    'color': 'white',
    'fontWeight': 'bold',
    'cursor': 'pointer',
    'boxSizing': 'border-box'
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

# Define the layout for the login page
layout = html.Div([
    dcc.Store(id="session", storage_type="session"),
    html.H1("Login", id='page-title', style={'textAlign': 'center'}),

    html.Div([
        # login fields
        html.Div([
            dcc.Input(placeholder='Username', type='text', id='username',
                      style=input_style),
            dcc.Input(placeholder='Password', type='password', id='password',
                      style=input_style),
        ], id='login-fields', style=field_group_style),

        # registration fields (initially hidden)
        html.Div([
            dcc.Input(placeholder='Email', type='email', id='email',
                      style=input_style),
            dcc.Input(placeholder='Confirm Password', type='password', id='confirm-password',
                      style={**input_style, 'marginTop': '10px'}),
        ], id='signup-fields', style={'display': 'none'}),

        # Buttons
        html.Button('Login', id='login-button', n_clicks=0, style=button_style),
        html.Button('Sign-in', id='signup-button', n_clicks=0,
                    style={'display': 'none',}),
        html.Button('Back to lognin', id='back-to-login', n_clicks=0,
                    style={'display': 'none'}),

        html.Div(id='login-output', style={'textAlign': 'center', 'color': 'red', 'marginTop': '10px'}),
        dcc.Store(id="session", storage_type="session") #

    ], style=form_card_style)
])

@callback(
    [Output('signup-fields', 'style'),
     Output('signup-button', 'style'),
     Output('back-to-login', 'style'),
     Output('login-button', 'style'),
     Output('page-title', 'children'),
     Output('login-output', 'children', allow_duplicate=True),
     Output('session', 'data')],#
    [Input('login-button', 'n_clicks'),
     Input('back-to-login', 'n_clicks')],
    [State('username', 'value'),
     State('password', 'value')],
    prevent_initial_call=True,
    allow_duplicate=True
)
def handle_login_and_show_signup(login_clicks, back_clicks, username, password):
    ctx = dash.callback_context # get the context of the triggered input
    if not ctx.triggered:
        return [{'display': 'none'}] * 3 + [{'display': 'block'}] + ["Login", ""]
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] # get the ID of the triggered input
    # If the user clicks "Back to login"
    if trigger_id == 'back-to-login':
        return (
            {'display': 'none'},  # signup-fields
            {**button_style,'display': 'none'},  # signup-button
            {'display': 'none'},  # back-to-login
            {**button_style,'display': 'block'}, # login-button
            "Login",              # page-title
            "",                   # login-output
            no_update
        )
    # If the user clicks "Login" and has entered username and password
    if trigger_id == 'login-button' and login_clicks > 0:
        if not username or not password:
            return [{'display': 'none'}] * 3 + [{'display': 'block'}] + ["Login", "Insert username e password"]
        try:
            res = requests.post("http://localhost:5001/api/login", json={
                "username": username,
                "password": password
            })
            if res.status_code == 200:
                return [{'display': 'none'}] * 3 + [{**button_style,'display': 'block'}] + ["Login", "Login successful!", {"logged_in": True, "username": username}]#
            elif res.status_code == 403:
                return [{'display': 'none'}] * 3 + [{**button_style,'display': 'block'}] + ["Login", "Wrong password.",dash.no_update]
            elif res.status_code == 401:
                # show sign in fields if the user is not registered
                return (
                    {'display': 'block'},  # signup-fields
                    {**button_style,'display': 'block'},  # sign in-button
                    {**button_style,'display': 'block'},  # back-to-login
                    {**button_style, 'display': 'none'},   # login-button
                    "Registration",       # page-title   
                    "Username not found. Please register.", # login-output
                    no_update
                )
            else:
                return [{'display': 'none'}] * 3 + [{'display': 'block'}] + ["Login", f"Errore: {res.status_code} - {res.text}",dash.no_update]     
        except requests.exceptions.RequestException as e:
            return [{'display': 'none'}] * 3 + [{'display': 'block'}] + ["Login", f"Errore di connessione: {str(e)}",dash.no_update]
    return [{'display': 'none'}] * 3 + [{'display': 'block'}] + ["Login", ""]

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
        # validation of the inputs
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
            # check the response status code
            # 200 or 201 for successful registration   
            if res.status_code == 200 or res.status_code == 201:
                return "Registartion completed! Now you can login."
            else:
                return f"Error in registration: {res.status_code} - {res.text}"      
        except requests.exceptions.RequestException as e:
            return f"Connection error: {str(e)}"
    return ""

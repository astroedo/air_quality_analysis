import dash
from dash import html, dcc, Input, Output, State, callback, no_update
import requests

dash.register_page(__name__, path='/login', name='Login')

# Styles
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
    dcc.Store(id='login-page-store', data={'mode': 'login'}),
    
    html.H1("Login", id='login-page-title', style={'textAlign': 'center'}),
    html.Div(id='login-user-info', style={'textAlign': 'center', 'marginBottom': '20px'}),

    html.Div([
        html.Div([
            dcc.Input(id='login-username', placeholder='Username', type='text', style=input_style),
            dcc.Input(id='login-password', placeholder='Password', type='password', style=input_style)
        ], id='login-fields', style=field_group_style),

        html.Div([
            dcc.Input(id='login-email', placeholder='Email', type='email', style=input_style),
            dcc.Input(id='login-confirm-password', placeholder='Confirm Password', type='password', style={**input_style, 'marginTop': '10px'})
        ], id='signup-fields', style={'display': 'none'}),

        html.Button('Login', id='login-button', n_clicks=0, style=button_style),
        html.Button('Sign-in', id='signup-button', n_clicks=0, style={'display': 'none'}),
        html.Button('Back to login', id='back-to-login', n_clicks=0, style={'display': 'none'})
    ], id='login-form-container', style=form_card_style),

    html.Div(id='login-output', style={'textAlign': 'center', 'color': 'red', 'marginTop': '10px'})
])

# Toggle login/signup view
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
    from dash import ctx
    if not ctx.triggered or not back_clicks or ctx.triggered[0]['prop_id'] == 'back-to-login.n_clicks':
        return (
            {'display': 'none'},
            {'display': 'none'},
            {'display': 'none'},
            {**button_style, 'display': 'block'},
            "Login",
            {'mode': 'login'}
        )
    return no_update

# Check session state
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
            {'display': 'none'},
            "Welcome to GeoAir!",
            f"You are logged in as {username}. Please, logout to switch user.",
            {'color': 'black', 'textAlign': 'center', 'marginTop': '20px', 'fontWeight': 'bold'}
        )
    return (
        form_card_style,
        "Login",
        "",
        no_update
    )

# Handle login action
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
    if not login_clicks:
        return no_update
    if not username or not password:
        return (
            no_update, no_update, no_update, no_update, no_update,
            "Insert username and password",
            {'color': 'red', 'textAlign': 'center', 'marginTop': '10px', 'fontWeight': 'bold'},
            no_update
        )
    try:
        res = requests.post("http://localhost:5001/api/login", json={
            "username": username,
            "password": password
        })
        if res.status_code == 200:
            return (
                {'display': 'none'}, {'display': 'none'}, {'display': 'none'},
                {**button_style, 'display': 'block'},
                f"Welcome, {username}!",
                "Login successful!",
                {'color': "#0ea80e", 'textAlign': 'center', 'marginTop': '10px', 'fontWeight': 'bold'},
                {"logged_in": True, "username": username}
            )
        elif res.status_code == 403:
            return (
                no_update, no_update, no_update, no_update, no_update,
                "Wrong password.",
                {'color': 'red', 'textAlign': 'center', 'marginTop': '10px', 'fontWeight': 'bold'},
                no_update
            )
        elif res.status_code == 401:
            return (
                {'display': 'block'},
                {**button_style, 'display': 'block'},
                {**button_style, 'display': 'block'},
                {'display': 'none'},
                "Registration",
                "Username not found. Please register.",
                {'color': 'red', 'textAlign': 'center', 'marginTop': '10px', 'fontWeight': 'bold'},
                no_update
            )
        else:
            return (
                no_update, no_update, no_update, no_update, no_update,
                f"Error: {res.status_code} - {res.text}",
                {'color': 'red', 'textAlign': 'center', 'marginTop': '10px', 'fontWeight': 'bold'},
                no_update
            )
    except requests.exceptions.RequestException as e:
        return (
            no_update, no_update, no_update, no_update, no_update,
            f"Connection error: {str(e)}",
            {'color': 'red', 'textAlign': 'center', 'marginTop': '10px', 'fontWeight': 'bold'},
            no_update
        )

# Handle signup action
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
    if not n_clicks:
        return no_update
    if not all([username, password, email, confirm_password]):
        return ("Please, fill all the fields.", 
                {'color': 'red', 'textAlign': 'center', 'marginTop': '10px', 'fontWeight': 'bold'})
    if password != confirm_password:
        return ("The passwords are different.", 
                {'color': 'red', 'textAlign': 'center', 'marginTop': '10px', 'fontWeight': 'bold'})
    try:
        res = requests.post("http://localhost:5001/api/signin", json={
            "username": username,
            "password": password,
            "email": email
        })
        if res.status_code in (200, 201):
            return ("Registration completed! Now you can login.", 
                    {'color': '#0ea80e', 'textAlign': 'center', 'marginTop': '10px', 'fontWeight': 'bold'})
        else:
            return (f"Error in registration: {res.status_code} - {res.text}", 
                    {'color': 'red', 'textAlign': 'center', 'marginTop': '10px', 'fontWeight': 'bold'})
    except requests.exceptions.RequestException as e:
        return (f"Connection error: {str(e)}", 
                {'color': 'red', 'textAlign': 'center', 'marginTop': '10px', 'fontWeight': 'bold'})

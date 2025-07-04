import dash
from dash import html, dcc, Input, Output, State, callback, no_update
import requests
from components.logger import logger

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



### LAYOUT -> LOGIN PAGE ###
layout = html.Div([
    dcc.Store(id='login-page-store', data={'mode': 'login'}),
    
    html.H1("Login", id='login-page-title', style={'textAlign': 'center',"fontSize": "32px", "color": "rgb(19, 129, 159)", "marginTop": "40px"}),
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




# Toggle between login and signup views
@callback(
    [
        Output('signup-fields', 'style'),      # Show/hide signup input fields
        Output('signup-button', 'style'),      # Show/hide signup button
        Output('back-to-login', 'style'),      # Show/hide "back to login" link
        Output('login-button', 'style'),       # Show/hide login button
        Output('login-page-title', 'children'),# Change login page title text
        Output('login-page-store', 'data')     # Store current mode ('login' or 'signup') in page store
    ],
    [
        Input('back-to-login', 'n_clicks'),    # Triggered when user clicks "back to login"
        Input('login-page-store', 'data')      # Current stored mode data
    ],
    prevent_initial_call='initial_duplicate'
)
def toggle_login_signup(back_clicks, store_data):
    from dash import ctx
    # If no trigger or user clicked "back to login"
    if not ctx.triggered or not back_clicks or ctx.triggered[0]['prop_id'] == 'back-to-login.n_clicks':
        # Switch view to login: hide signup fields/buttons, show login button, update title and mode
        return (
            {'display': 'none'},        # Hide signup fields
            {'display': 'none'},        # Hide signup button
            {'display': 'none'},        # Hide back-to-login link
            {**button_style, 'display': 'block'},  # Show login button
            "Login",                   # Set page title to "Login"
            {'mode': 'login'}          # Update store mode to 'login'
        )
    # If other triggers occur, do nothing (no update)
    return no_update



# Check if user session is active and update login form accordingly
@callback(
    [
        Output('login-form-container', 'style'),       # Show/hide login form container
        Output('login-page-title', 'children', allow_duplicate=True),  # Update page title
        Output('login-output', 'children', allow_duplicate=True),     # Show login status message
        Output('login-output', 'style', allow_duplicate=True)         # Style for login status message
    ],
    Input('session', 'data'),  # Triggered when session data changes
    prevent_initial_call='initial_duplicate',
    allow_duplicate=True
)
def check_login_status(session_data):
    # If session exists and user is logged in
    if session_data and session_data.get("logged_in", False):
        username = session_data.get("username", "unknown user")
        # Hide login form and show welcome message with username
        return (
            {'display': 'none'},      # Hide login form
            "Welcome to GeoAir!",     # Change page title to welcome message
            f"You are logged in as {username}. Please, logout to switch user.",  # Status message
            {'color': 'black', 'textAlign': 'center', 'marginTop': '20px', 'fontWeight': 'bold'}  # Styling message
        )
    # If not logged in, show login form with default title and no message
    return (
        form_card_style,             # Show login form with default style
        "Login",                    # Page title as "Login"
        "",                         # No status message
        no_update                   # Keep previous style for status message
    )


# Handle login action callback
@callback(
    [
        Output('signup-fields', 'style', allow_duplicate=True),  # Show/hide signup fields
        Output('signup-button', 'style', allow_duplicate=True),  # Show/hide signup button
        Output('back-to-login', 'style', allow_duplicate=True),  # Show/hide back to login link
        Output('login-button', 'style', allow_duplicate=True),   # Show/hide login button
        Output('login-page-title', 'children', allow_duplicate=True),  # Change page title text
        Output('login-output', 'children', allow_duplicate=True),      # Display login status message
        Output('login-output', 'style', allow_duplicate=True),         # Style of login status message
        Output('session', 'data', allow_duplicate=True)                 # Update session data on successful login
    ],
    Input('login-button', 'n_clicks'),  # Triggered when login button is clicked
    [
        State('login-username', 'value'),  # Current username input
        State('login-password', 'value'),  # Current password input
        State('session', 'data')            # Current session data
    ],
    prevent_initial_call=True,
    allow_duplicate=True
)
def handle_login(login_clicks, username, password, session_data):
    if not login_clicks:
        return no_update  # Do nothing if login button not clicked

    # Validate username and password presence
    if not username or not password:
        # Prompt user to insert credentials if missing
        return (
            no_update, no_update, no_update, no_update, no_update,
            "Insert username and password",
            {'color': 'red', 'textAlign': 'center', 'marginTop': '10px', 'fontWeight': 'bold'},
            no_update
        )

    try:
        # Send POST request to login API with username and password
        res = requests.post("http://localhost:5001/api/login", json={
            "username": username,
            "password": password
        })

        if res.status_code == 200:
            # Login successful: hide signup elements, show welcome message, update session
            logger.info(f"User {username} logged in successfully.")
            # Update session data with login status and username
            return (
                {'display': 'none'}, {'display': 'none'}, {'display': 'none'},
                {**button_style, 'display': 'block'},
                f"Welcome, {username}!",
                "Login successful!",
                {'color': "#0ea80e", 'textAlign': 'center', 'marginTop': '10px', 'fontWeight': 'bold'},
                {"logged_in": True, "username": username}
            )
        elif res.status_code == 403:
            # Wrong password response: show error message
            logger.warning(f"Failed login attempt for user {username}: wrong password.")
            return (
                no_update, no_update, no_update, no_update, no_update,
                "Wrong password.",
                {'color': 'red', 'textAlign': 'center', 'marginTop': '10px', 'fontWeight': 'bold'},
                no_update
            )
        elif res.status_code == 401:
            # Username not found: show signup fields, prompt registration
            logger.warning(f"User {username} not found.")
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
            # Other error responses: display error status and message
            logger.error(f"Login failed for user {username}: {res.status_code} - {res.text}")
            return (
                no_update, no_update, no_update, no_update, no_update,
                f"Error: {res.status_code} - {res.text}",
                {'color': 'red', 'textAlign': 'center', 'marginTop': '10px', 'fontWeight': 'bold'},
                no_update
            )
    except requests.exceptions.RequestException as e:
        # Connection or request error: display connection error message
        logger.error(f"Connection error during login for user {username}: {str(e)}")
        return (
            no_update, no_update, no_update, no_update, no_update,
            f"Connection error: {str(e)}",
            {'color': 'red', 'textAlign': 'center', 'marginTop': '10px', 'fontWeight': 'bold'},
            no_update
        )


# Handle signup action callback
@callback(
    [
        Output('login-output', 'children', allow_duplicate=True),  # Show signup status message
        Output('login-output', 'style', allow_duplicate=True)      # Style signup status message
    ],
    Input('signup-button', 'n_clicks'),  # Triggered when signup button clicked
    [
        State('login-username', 'value'),         # Username input during signup
        State('login-password', 'value'),         # Password input during signup
        State('login-email', 'value'),             # Email input during signup
        State('login-confirm-password', 'value')  # Confirm password input during signup
    ],
    prevent_initial_call=True,
    allow_duplicate=True
)
def handle_signin(n_clicks, username, password, email, confirm_password):
    if not n_clicks:
        return no_update  # Do nothing if signup button not clicked

    # Validate that all fields are filled
    if not all([username, password, email, confirm_password]):
        return (
            "Please, fill all the fields.",
            {'color': 'red', 'textAlign': 'center', 'marginTop': '10px', 'fontWeight': 'bold'}
        )

    # Validate password confirmation matches
    if password != confirm_password:
        return (
            "The passwords are different.",
            {'color': 'red', 'textAlign': 'center', 'marginTop': '10px', 'fontWeight': 'bold'}
        )

    try:
        # Send POST request to signup API with registration data
        res = requests.post("http://localhost:5001/api/signin", json={
            "username": username,
            "password": password,
            "email": email
        })

        if res.status_code in (200, 201):
            logger.info(f"User {username} registered successfully.")
            # Successful registration: notify user they can login now
            return (
                "Registration completed! Now you can login.",
                {'color': '#0ea80e', 'textAlign': 'center', 'marginTop': '10px', 'fontWeight': 'bold'}
            )
        else:
            logger.error(f"Registration failed for user {username}: {res.status_code} - {res.text}")
            # Registration error: display error message from server
            return (
                f"Error in registration: {res.status_code} - {res.text}",
                {'color': 'red', 'textAlign': 'center', 'marginTop': '10px', 'fontWeight': 'bold'}
            )
    except requests.exceptions.RequestException as e:
        logger.error(f"Connection error during signup for user {username}: {str(e)}")
        # Connection error during signup: show error message
        return (
            f"Connection error: {str(e)}",
            {'color': 'red', 'textAlign': 'center', 'marginTop': '10px', 'fontWeight': 'bold'}
        )

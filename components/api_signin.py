"""
API sign-in helper.

Sends a POST request to the sign-in endpoint and returns the result message.
Logs warnings and errors when appropriate.
"""

import requests
from components.logger import logger

def api_signin(username, password, email, confirm_password):
    """
    Validates input and sends a sign-in request.
    Returns a response string for display.
    """
    if not all([username, password, email, confirm_password]):
        return "Please, fill all the fields."
    if password != confirm_password:
        return "The passwords are different."
    try:
        response = requests.post("http://localhost:5000/api/signin", json={
            "username": username,
            "password": password,
            "email": email
        })
        if response.status_code in (200, 201):
            return "Registration completed! Now you can log in."
        return f"Error in registration: {response.status_code} - {response.text}"
    except requests.exceptions.RequestException as e:
        logger.error(f"Sign-in API request failed: {e}")
        return f"Connection error: {str(e)}"

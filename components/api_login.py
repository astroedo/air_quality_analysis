"""
API login helper.

Sends a POST request to the login API endpoint and returns the response status and text.
Logs warnings and errors when appropriate.
"""

import requests
from components.logger import logger

def api_login(username, password):
    if not username or not password:
        logger.warning("Login attempt with missing credentials.")
        return {"status": "missing", "text": "Username and password required."}

    try:
        url = "http://localhost:5000/api/login"
        response = requests.post(url, json={"username": username, "password": password})
        return {"status": response.status_code, "text": response.text}
    except requests.exceptions.RequestException as e:
        logger.error(f"Login API request failed: {e}")
        return {"status": "error", "text": str(e)}
    

    

def get_login_response_ui(result):
    status = result["status"]
    text = result["text"]

    if status == "missing":
        return [{'display': 'none'}] * 3 + [{'display': 'block'}] + ["Login", "Please enter username and password."]
    if status == 200:
        return [{'display': 'none'}] * 3 + [{'display': 'block'}] + ["Login", "Login successful!"]
    if status == 403:
        return [{'display': 'none'}] * 3 + [{'display': 'block'}] + ["Login", "Wrong password."]
    if status == 401:
        return (
            {'display': 'block'},  # signup-fields
            {'display': 'block'},  # signup-button
            {'display': 'block'},  # back-to-login
            {'display': 'none'},   # login-button
            "Registration",        # page-title
            "Username not found. Please register."  # login-output
        )
    if status == "error":
        return [{'display': 'none'}] * 3 + [{'display': 'block'}] + ["Login", f"Connection error: {text}"]

    return [{'display': 'none'}] * 3 + [{'display': 'block'}] + ["Login", f"Unexpected error: {text}"]

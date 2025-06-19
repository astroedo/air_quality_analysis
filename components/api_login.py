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
    


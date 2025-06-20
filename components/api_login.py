"""
API login helper.

Sends a POST request to the login API endpoint and returns the response status and text.
Maintains session using requests.Session for authenticated requests.
Logs warnings and errors when appropriate.
"""

import requests
from components.logger import logger

# Global session object to persist cookies across requests
session = requests.Session()

def api_login(username, password):
    if not username or not password:
        logger.warning("Login attempt with missing credentials.")
        return {"status": "missing", "text": "Username and password required."}

    try:
        url = "http://localhost:5000/api/login"
        response = session.post(
            url,
            json={"username": username, "password": password}
        )
        logger.info(f"Login attempt for '{username}' returned {response.status_code}")
        return {
            "status": response.status_code,
            "text": response.json().get("message", ""),
            "username": response.json().get("username", None)
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Login API request failed: {e}")
        return {"status": "error", "text": str(e)}

# Optional helper if you want to check current session later
def get_logged_user():
    try:
        response = session.get("http://localhost:5000/api/me")
        if response.status_code == 200:
            return response.json().get("username")
    except Exception as e:
        logger.warning(f"Could not fetch session user: {e}")
    return None

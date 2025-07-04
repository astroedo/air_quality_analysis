"""
Fetch pollutant data from the API.
Returns a pandas DataFrame with station data filtered by pollutant if specified.
Logs errors if the fetch fails.
"""

import pandas as pd
import requests
from components.logger import logger

def fetch_pollutant(pollutant=None):
    try:
        url = "http://localhost:5001/api/stations"
        if pollutant:
            url += f"?pollutant={pollutant}"
        response = requests.get(url)
        response.raise_for_status()
        
        logger.info(f"Filter: '{pollutant}' - Stations data fetched successfully")
        return pd.DataFrame(response.json())
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        return pd.DataFrame()


"""
# Example of usage:
from functions.fetch_pollutant import fetch_pollutant
data_all = fetch_pollutant()                # Fetch all data
data_pm10 = fetch_pollutant("PM10")         # Fetch only PM10 pollutant data
"""

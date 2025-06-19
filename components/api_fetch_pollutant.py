"""
Fetch pollutant data from the API.
Returns a pandas DataFrame with station data filtered by pollutant if specified.
Logs errors if the fetch fails.
"""

import pandas as pd
import requests
from components.logger import logger

def api_fetch_pollutant(pollutant=None):
    try:
        url = "http://localhost:5000/api/stations"
        if pollutant:
            url += f"?pollutant={pollutant}"
        response = requests.get(url)
        response.raise_for_status()
        return pd.DataFrame(response.json())
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        return pd.DataFrame()


"""
# Example of usage:
from components.api_fetch_pollutant import api_fetch_pollutant

df_all = api_fetch_pollutant()              # Fetch all data
df_pm10 = api_fetch_pollutant("PM10")        # Fetch only PM10 pollutant data

print(df_all.head())
print(df_pm10.head())
"""

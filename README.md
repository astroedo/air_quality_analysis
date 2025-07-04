# GeoAir 

GeoAir is a comprehensive web-based platform for analyzing and visualizing air quality data across the Lombardia region of Italy. Built with modern web technologies, it provides interactive maps, trend analysis, and real-time data visualization to support environmental decision-making.

# Key features 
## Interactive Geospatial Visualization
* Dynamic Province Maps: Color-coded pollution levels with historical data overlays
* Station Mapping: Interactive markers showing sensor locations and pollutant types
* Downloadable Shapefiles: Export map data for GIS analysis

## Advanced Analytics Dashboard
* Multi-pollutant Comparison: Analyze multiple pollutants simultaneously
* Temporal Trend Analysis: Historical data with smoothing options (7-day, 14-day averages)
* Statistical Summaries: Min, max, average, and data point counts
* Specialized Analysis: Dedicated tools for different compounds

## User management
* Session Management: Persistent user sessions

# Quick Start

## 1. Clone the Repository
```bash
git clone https://github.com/astroedo/air_quality_analysis.git
cd air_quality_analysis
```
## 2. Install Dependencies
```bash
pip install -r requirements.txt
```

## 3. Configure Database
```bash
# Create PostgreSQL database
createdb lombardia_air_quality

# Create user
psql -c "CREATE USER airdata_user WITH PASSWORD 'user';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE lombardia_air_quality TO airdata_user;"
```

## 4. Initialize Database
```bash
# Run Jupyter notebooks in order:
jupyter notebook database/database_user.ipynb
jupyter notebook database/database_station.ipynb
jupyter notebook database/database_measurement.ipynb
```

## 5. Launch Application
```bash
# Terminal 1: Start Flask API server
python server.py

# Terminal 2: Start Dash frontend  
python app.py
```

## 6. Access Application
Open your browser and navigate to:
```
http://localhost:8000
```
# Data Sources 
The platform integrates data from Dati Lombardia, the official open data portal of the Lombardy region:

## Station Data: Air Quality Stations

Station locations, sensor types, administrative info
API: https://www.dati.lombardia.it/resource/ib47-atvt.json


## Measurement Data: Air Sensor Data from 2018

Historical measurements
API: https://www.dati.lombardia.it/resource/g2hp-ar79.json


# Support
If you encounter any issues or have questions:

1. Create a new issue with detailed information
2. Contact the development team

# Acknowledgments

* Regione Lombardia for providing open air quality data
* Dati Lombardia platform for data accessibility


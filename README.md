# Air Quality Analysis 🍃

Italian public authorities collect, process, and analyze air quality data to monitor pollution levels and their impact on public health. By combining air pollution data with sensor and administrative datasets, decision-makers (such as environmental agencies and public health organizations) can better understand pollution trends and exposure risks. The aim of this project is to visualize and analyze air quality data from Dati Lombardia to assess pollution levels and trends at different administrative levels within the region.

## Project Goals:
You are asked to develop a client-server application that supports users in querying and visualizing data retrieved from the Dati Lombardia air quality sensor dataset. The system should integrate and process real-time or historical air quality measurements to provide insights into pollution distribution, trends, and exposure risks.








Project API
measurement: https://www.dati.lombardia.it/Ambiente/Dati-sensori-aria-dal-2018/g2hp-ar79/about_data
API:         https://www.dati.lombardia.it/resource/g2hp-ar79.json
    idsensore, data, valore, stato, idoperatore

station:     https://www.dati.lombardia.it/Ambiente/Stazioni-qualit-dell-aria/ib47-atvt/about_data
API:         https://www.dati.lombardia.it/resource/ib47-atvt.json
    idsensore, nometiposensore, unitamisura, idstazione, nomestazione,
    quota, provincia, comune, storico, datastart, datastop, utm_nord,
    utm_est, lat, lng, locationtxt, location(geometry:point)

N.B. API format: .csv .json .geojson 
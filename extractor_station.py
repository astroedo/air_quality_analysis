import requests
from datetime import datetime
from db_connection import get_db_connection
from db_station import create_station_table

BASE_URL_STATION = "https://www.dati.lombardia.it/resource/ib47-atvt.json"

def get_filtered_station_data(limit=200):
    url = f"{BASE_URL_STATION}?$limit={limit}"
    print(f"Chiamata API (stazioni): {url}")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        print(f"Ricevuti {len(data)} record stazioni.")
        return data
    except requests.RequestException as e:
        print(f"Errore nella richiesta API stazioni: {e}")
        return []

def count_existing_rows(conn):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM stazioni_aria")
    count = cur.fetchone()[0]
    cur.close()
    return count

def insert_station_data(conn, data):
    cur = conn.cursor()
    insert_rows = []

    for r in data:
        try:
            datastart = datetime.fromisoformat(r.get('datastart')) if r.get('datastart') else None
            datastop = datetime.fromisoformat(r.get('datastop')) if r.get('datastop') else None

            insert_rows.append((
                r.get('idsensore'),
                r.get('nometiposensore'),
                r.get('unitamisura'),
                r.get('idstazione'),
                r.get('nomestazione'),
                r.get('quota'),
                r.get('provincia'),
                r.get('comune'),
                r.get('storico'),
                datastart,
                datastop,
                r.get('utm_nord'),
                r.get('utm_est'),
                r.get('lat'),
                r.get('lng'),
                str(r.get('location'))  # location è un oggetto GeoJSON, semplificato in stringa
            ))
        except Exception as e:
            print(f"Errore parsing record stazione: {e}")

    if insert_rows:
        count_before = count_existing_rows(conn)

        cur.executemany("""
            INSERT INTO stazioni_aria (
                idsensore, nometiposensore, unitamisura, idstazione, nomestazione, quota,
                provincia, comune, storico, datastart, datastop, utm_nord, utm_est,
                lat, lng, location
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (idsensore, datastart) DO NOTHING
        """, insert_rows)

        conn.commit()

        count_after = count_existing_rows(conn)
        added = count_after - count_before
        print(f"Inseriti {added} nuovi record stazioni su {len(insert_rows)} totali.")
    else:
        print("Nessun dato valido da inserire.")

    cur.close()

def update_station_data():
    conn = get_db_connection()
    create_station_table()

    data = get_filtered_station_data(limit=200)
    if data:
        insert_station_data(conn, data)
    else:
        print("Nessun nuovo record stazione trovato.")

    conn.close()

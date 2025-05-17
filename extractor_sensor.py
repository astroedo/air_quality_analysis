import requests
from datetime import datetime
from db_connection import get_db_connection
from db_sensor import create_sensor_table

BASE_URL_SENSOR = "https://www.dati.lombardia.it/resource/g2hp-ar79.json"

def get_filtered_sensor_data(limit=30):
    url = f"{BASE_URL_SENSOR}?$order=data DESC&$limit={limit}"
    print(f"Chiamata API (sensori): {url}")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        print(f"Ricevuti {len(data)} record sensori.")
        return data
    except requests.RequestException as e:
        print(f"Errore nella richiesta API sensori: {e}")
        return []

def get_last_sensor_date(conn):
    cur = conn.cursor()
    cur.execute("SELECT MAX(data) FROM sensori_aria")
    result = cur.fetchone()
    cur.close()
    return result[0]

def insert_sensor_data(conn, data):
    cur = conn.cursor()
    insert_rows = []

    for r in data:
        try:
            dt = datetime.strptime(r.get('data'), "%Y-%m-%dT%H:%M:%S.%f")
            insert_rows.append((
                r.get('idsensore'),
                dt,
                r.get('valore'),
                r.get('stato'),
                r.get('idoperatore')
            ))
        except Exception as e:
            print(f"Errore parsing record sensore: {e}")

    if insert_rows:
        cur.executemany("""
            INSERT INTO sensori_aria (idsensore, data, valore, stato, idoperatore)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (idsensore, data) DO NOTHING
        """, insert_rows)

    conn.commit()
    cur.close()

def update_last_30_data():
    conn = get_db_connection()
    create_sensor_table()

    last_date = get_last_sensor_date(conn)
    if last_date is None:
        print("DB sensori vuoto. Carico gli ultimi 30 dati...")
    else:
        print("DB sensori già popolato. Verifico nuovi record...")

    data = get_filtered_sensor_data(limit=30)
    if data:
        insert_sensor_data(conn, data)
        print(f"Inseriti {len(data)} nuovi record sensori.")
    else:
        print("Nessun nuovo record sensore trovato.")

    conn.close()

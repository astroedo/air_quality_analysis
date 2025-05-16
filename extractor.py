import requests
from datetime import datetime
from db import get_db_connection, create_table_if_not_exists

def get_filtered_data(base_url, limit=30):
    # Costruisci l'URL per richiedere i dati ordinati per data decrescente e limitati ai primi 30
    url = f"{base_url}?$order=data DESC&$limit={limit}"
    print(f"Chiamata API: {url}")
    
    try:
        # Fai la richiesta all'API
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Verifica se la richiesta è andata a buon fine
        
        # Converte la risposta in formato JSON
        data = response.json()
        print(f"Ricevuti {len(data)} record.")
        
        return data
    except requests.RequestException as e:
        print(f"Errore durante la richiesta: {e}")
        return []


def get_last_date_in_db(conn):
    cur = conn.cursor()
    cur.execute("SELECT MAX(data) FROM sensori_aria")
    result = cur.fetchone()
    cur.close()
    return result[0]  # può essere None

def insert_new_data(conn, dati_aria):
    cur = conn.cursor()
    insert_data = []

    for record in dati_aria:
        try:
            data_originale = datetime.strptime(record.get('data'), "%Y-%m-%dT%H:%M:%S.%f")
            insert_data.append((
                record.get('idsensore'),
                data_originale,
                record.get('valore'),
                record.get('stato'),
                record.get('idoperatore')
            ))
        except Exception as e:
            print(f"Errore nella conversione di un record: {e}")

    if insert_data:
        cur.executemany("""
            INSERT INTO sensori_aria (idsensore, data, valore, stato, idoperatore)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (idsensore, data) DO NOTHING
        """, insert_data)

    conn.commit()
    cur.close()

def update_last_30_data():
    conn = get_db_connection()
    create_table_if_not_exists(conn)

    last_date = get_last_date_in_db(conn)
    base_url = "https://www.dati.lombardia.it/resource/g2hp-ar79.json"

    if last_date is None:
        print("Nessun dato nel database. Scarico gli ultimi 30 record...")
    else:
        print("Database già popolato. Cerco eventuali nuovi record recenti...")

    new_data = get_filtered_data(base_url, limit=30)

    if not new_data:
        print("Nessun nuovo dato trovato.")
    else:
        insert_new_data(conn, new_data)
        print(f"Aggiunti {len(new_data)} nuovi record.")

    conn.close()
    print("Aggiornamento completato.")

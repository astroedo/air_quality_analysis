import requests
from datetime import datetime
from extra.db_connection import get_db_connection

# URL per l'API dei sensori
BASE_URL_SENSOR = "https://www.dati.lombardia.it/resource/g2hp-ar79.json"


# Funzione per creare la tabella sensori nel database
def sensor_create_table():
    """
    Crea la tabella sensori_aria nel database se non esiste.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sensori_aria (
            id SERIAL PRIMARY KEY,
            idsensore TEXT,
            data TIMESTAMP,
            valore NUMERIC,
            stato TEXT,
            idoperatore TEXT,
            UNIQUE (idsensore, data)
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

# Funzione per eliminare completamente la tabella sensori_aria
def sensor_drop_table():
    """
    Elimina completamente la tabella sensori_aria dal database.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS sensori_aria")  # Elimina la tabella se esiste
    conn.commit()
    cur.close()
    conn.close()



# Funzione per ottenere i dati sensori filtrati (limite per numero di record)
def sensor_get_filtered_data(limit=30):
    """
    Recupera i dati dei sensori dall'API, limitando il numero di record.
    """
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


# Funzione per ottenere la data dell'ultimo dato sensore dal database
def sensor_get_last_date(conn):
    """
    Ottiene la data dell'ultimo record sensore presente nel database.
    """
    cur = conn.cursor()
    cur.execute("SELECT MAX(data) FROM sensori_aria")
    result = cur.fetchone()
    cur.close()
    return result[0]


# Funzione per inserire i dati sensori nel database
def sensor_insert_data(conn, data):
    """
    Inserisce i dati sensori nel database.
    """
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


# Funzione per aggiornare i dati degli ultimi 30 sensori
def sensor_update_data():
    """
    Aggiorna i dati dei sensori nel database, inserendo gli ultimi 30 record.
    """
    conn = get_db_connection()
    sensor_create_table()  # Assicurati che la tabella esista

    last_date = sensor_get_last_date(conn)
    if last_date is None:
        print("DB sensori vuoto. Carico gli ultimi 30 dati...")
    else:
        print("DB sensori già popolato. Verifico nuovi record...")

    data = sensor_get_filtered_data(limit=30)
    if data:
        sensor_insert_data(conn, data)
        print(f"Inseriti {len(data)} nuovi record sensori.")
    else:
        print("Nessun nuovo record sensore trovato.")

    conn.close()  # Chiudi la connessione al database



# Funzione per eliminare gli ultimi n record sensori
def sensor_delete_n_records(n=10):
    """
    Elimina gli ultimi n record sensori dal database.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(f"""
        DELETE FROM sensori_aria
        WHERE id IN (
            SELECT id FROM sensori_aria
            ORDER BY data DESC
            LIMIT {n}
        )
    """)

    conn.commit()
    cur.close()
    conn.close()


# Funzione per contare il numero di righe nella tabella sensori_aria
def sensor_count_records():
    """
    Conta il numero di record nella tabella sensori_aria, distingue tra tabella vuota e tabella non esistente.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Verifica se la tabella esiste
    cur.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'sensori_aria' AND table_schema = 'public')")
    table_exists = cur.fetchone()[0]
    
    if not table_exists:
        # La tabella non esiste
        cur.close()
        conn.close()
        return "Tabella non esistente"
    
    # La tabella esiste, ora conta il numero di righe
    cur.execute("SELECT COUNT(*) FROM sensori_aria")
    result = cur.fetchone()[0]
    
    cur.close()
    conn.close()
    
    if result == 0:
        # La tabella è vuota
        return "Tabella vuota"
    
    # La tabella contiene record
    return result




# Funzione per chiedere all'utente se vuole creare, eliminare o eliminare un numero specifico di righe
def sensor_manage_database():
    """
    Chiede all'utente se vuole creare o eliminare la tabella del database e le relative tabelle.
    """
    print("Stato della tabella sensori:", sensor_count_records())
    
    action = input("Vuoi creare o eliminare la tabella del database? (creare/eliminare/eliminare_n): ").strip().lower()

    if action == "creare":
        print("Creazione della tabella sensori...")
        sensor_create_table()
        print("Tabella sensori creata con successo!")
    elif action == "eliminare":
        print("Eliminazione della tabella sensori...")
        sensor_drop_table()
        print("Tabella sensori eliminata con successo!")
    elif action.startswith("eliminare_n"):
        try:
            n = int(action.split('_')[-1]) if len(action.split('_')) > 1 else 10
            print(f"Eliminazione degli ultimi {n} record sensori...")
            sensor_delete_n_records(n)
            print(f"Eliminati gli ultimi {n} record sensori con successo!")
        except ValueError:
            print("Input non valido. Inserisci un numero valido di righe da eliminare.")
    else:
        print("Azione non valida. Per favore, inserisci 'creare', 'eliminare' o 'eliminare_n'.")



# python -m functions.sensor_management
if __name__ == "__main__":
    sensor_manage_database()


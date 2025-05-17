import psycopg2
from datetime import datetime

def insert_station_data(conn, dati_stazione):
    cur = conn.cursor()
    insert_data = []
    
    for record in dati_stazione:
        try:
            # Convertiamo 'datastart' e 'datastop' a formato datetime
            datastart = datetime.strptime(record.get("datastart"), "%Y-%m-%dT%H:%M:%S") if record.get("datastart") else None
            datastop = datetime.strptime(record.get("datastop"), "%Y-%m-%dT%H:%M:%S") if record.get("datastop") else None
            
            insert_data.append((
                record.get("idsensore"),
                record.get("nometiposensore"),
                record.get("unitamisura"),
                record.get("idstazione"),
                record.get("nomestazione"),
                record.get("quota"),
                record.get("provincia"),
                record.get("comune"),
                record.get("storico"),
                datastart,
                datastop,
                record.get("utm_nord"),
                record.get("utm_est"),
                record.get("lat"),
                record.get("lng"),
                record.get("location")
            ))
        except Exception as e:
            print(f"Errore nella conversione di un record: {e}")
    
    if insert_data:
        cur.executemany("""
            INSERT INTO stazioni_aria (idsensore, nometiposensore, unitamisura, idstazione, nomestazione, quota, provincia, comune, storico, datastart, datastop, utm_nord, utm_est, lat, lng, location)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (idsensore, datastart) DO NOTHING  -- evitare duplicati
        """, insert_data)

    conn.commit()
    cur.close()

from db_connection import get_db_connection

def elimina_ultimi_10_stazioni():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM stazioni_aria
        WHERE id IN (
            SELECT id FROM stazioni_aria
            ORDER BY id DESC
            LIMIT 10
        )
    """)

    conn.commit()
    cur.close()
    conn.close()

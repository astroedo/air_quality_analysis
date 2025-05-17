# db_station.py
from db_connection import get_db_connection

def create_station_table():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stazioni_aria (
            id SERIAL PRIMARY KEY,
            idsensore TEXT,
            nometiposensore TEXT,
            unitamisura TEXT,
            idstazione TEXT,
            nomestazione TEXT,
            quota TEXT,
            provincia TEXT,
            comune TEXT,
            storico TEXT,
            datastart TIMESTAMP,
            datastop TIMESTAMP,
            utm_nord TEXT,
            utm_est TEXT,
            lat NUMERIC,
            lng NUMERIC,
            location TEXT,
            UNIQUE (idsensore, datastart)
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    create_station_table()
    print("Tabella 'stazioni_aria' creata (se non esiste già).")

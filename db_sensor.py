# crate table sensori_aria
from db_connection import get_db_connection

def create_sensor_table():
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

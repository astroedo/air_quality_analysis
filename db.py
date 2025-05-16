import psycopg2

def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="se4gProject",
        user="se4g",
        password="admin"
    )

def create_table_if_not_exists(conn):
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

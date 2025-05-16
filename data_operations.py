from db import get_db_connection

def elimina_ultimi_10_record():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM sensori_aria
        WHERE id IN (
            SELECT id FROM sensori_aria
            ORDER BY data DESC
            LIMIT 10
        )
    """)

    conn.commit()
    cur.close()
    conn.close()

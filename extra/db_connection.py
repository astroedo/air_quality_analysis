# CHECK CONNECTION WITH: python db_connection.py
import psycopg2

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="se4gProject",
            user="se4g",
            password="admin"
        )
        print("Connessione riuscita!")  # Aggiungi il print qui quando la connessione ha successo
        return conn
    except Exception as e:
        print(f"Errore nella connessione al database: {e}")  # Aggiungi il print per l'errore
        return None

# Se vuoi eseguire il test della connessione quando esegui il file direttamente, puoi farlo qui:
if __name__ == "__main__":
    conn = get_db_connection()
    if conn:
        conn.close()
    else:
        print("Connessione fallita.")

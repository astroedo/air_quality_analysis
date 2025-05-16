import psycopg2

def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="se4gProject",
        user="se4g",
        password="admin"
    )

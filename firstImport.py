import requests
import psycopg2

# ✅ Connessione al database
mydb = psycopg2.connect(
    host="localhost",
    database="se4gProject",
    user="se4g",
    password="admin"
)
cursor = mydb.cursor()

# ✅ Imposta le date come variabili
data_inizio = "2024-12-01T00:00:00"
data_fine = "2024-12-31T23:59:59"

# ✅ Funzione per scaricare dati con intervallo data e paginazione
def get_filtered_data(base_url, where_filter):
    all_data = []
    offset = 0
    limit = 1000

    while True:
        url = f"{base_url}?$where={where_filter}&$limit={limit}&$offset={offset}"
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Errore richiesta offset {offset}: {response.status_code}")
            break
        data = response.json()
        if not data:
            break
        all_data.extend(data)
        offset += limit
    return all_data

# ✅ Download dati filtrati per data
where_clause = f"data between '{data_inizio}' and '{data_fine}'"
base_url_aria = "https://www.dati.lombardia.it/resource/g2hp-ar79.json"
dati_aria = get_filtered_data(base_url_aria, where_clause)

# ✅ Download dati stazioni (non serve filtro perché sono statici)
response_stazioni = requests.get("https://www.dati.lombardia.it/resource/ib47-atvt.json")
dati_stazioni = response_stazioni.json() if response_stazioni.status_code == 200 else []

# ✅ Creazione delle tabelle (se non esistono)
cursor.execute("""
    CREATE TABLE IF NOT EXISTS sensori_aria (
        id SERIAL PRIMARY KEY,
        idsensore TEXT,
        data TIMESTAMP,
        valore NUMERIC,
        stato TEXT,
        idoperatore TEXT
    )
""")

cursor.execute("""
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
        datastart DATE,
        datastop DATE,
        utm_nord TEXT,
        utm_est TEXT,
        lat NUMERIC,
        lng NUMERIC
    )
""")

mydb.commit()

# ✅ Inserimento dati sensori aria nel database
for record in dati_aria:
    cursor.execute("""
        INSERT INTO sensori_aria (idsensore, data, valore, stato, idoperatore)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        record.get('idsensore'),
        record.get('data'),
        record.get('valore'),
        record.get('stato'),
        record.get('idoperatore')
    ))

# ✅ Inserimento dati stazioni nel database
for record in dati_stazioni:
    cursor.execute("""
        INSERT INTO stazioni_aria (
            idsensore, nometiposensore, unitamisura,
            idstazione, nomestazione, quota, provincia,
            comune, storico, datastart, datastop,
            utm_nord, utm_est, lat, lng
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        record.get('idsensore'),
        record.get('nometiposensore'),
        record.get('unitamisura'),
        record.get('idstazione'),
        record.get('nomestazione'),
        record.get('quota'),
        record.get('provincia'),
        record.get('comune'),
        record.get('storico'),
        record.get('datastart'),
        record.get('datastop'),
        record.get('utm_nord'),
        record.get('utm_est'),
        record.get('lat'),
        record.get('lng')
    ))

# ✅ Commit finale e chiusura
mydb.commit()
cursor.close()
mydb.close()

print(f"Inseriti {len(dati_aria)} record dei sensori e {len(dati_stazioni)} stazioni.")

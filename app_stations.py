from flask import Flask, render_template, redirect, url_for
from extractor_station import get_station_data_from_api, process_station_data
from data_operations_station import insert_station_data
from db import get_db_connection

app = Flask(__name__)

@app.route('/')
def index():
    return redirect(url_for('visualization_station'))

@app.route('/visualization_station')
def visualization_station():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT idsensore, datastart, nomestazione, provincia
        FROM stazioni_aria 
        ORDER BY datastart DESC 
        LIMIT 100
    """)
    dati = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('visualization_station.html', dati=dati)

@app.route('/aggiorna-dati-stazione', methods=['POST'])
def aggiorna_dati_stazione():
    conn = get_db_connection()
    
    # Ottieni i dati delle stazioni e processali
    data = get_station_data_from_api()
    processed_data = process_station_data(data)
    
    if processed_data:
        insert_station_data(conn, processed_data)
        print(f"Aggiunti {len(processed_data)} nuovi record delle stazioni.")
    
    conn.close()
    return redirect(url_for('visualization_station'))

@app.route('/elimina-ultimi-10-stazione', methods=['POST'])
def elimina_ultimi_10_stazione():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Elimina i 10 record più recenti delle stazioni
    cur.execute("""
        DELETE FROM stazioni_aria
        WHERE id IN (
            SELECT id FROM stazioni_aria
            ORDER BY datastart DESC
            LIMIT 10
        )
    """)
    
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('visualization_station'))

if __name__ == '__main__':
    app.run(debug=True)

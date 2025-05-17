from flask import Flask, render_template, redirect, url_for
from extractor_sensor import update_last_30_data
from extractor_station import update_station_data
from data_operations_sensor import elimina_ultimi_10_record
from data_operations_station import elimina_ultimi_10_stazioni
from db import get_db_connection

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/visualization_sensor')
def visualization_sensor():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT idsensore, data, valore, stato 
        FROM sensori_aria 
        ORDER BY data DESC 
        LIMIT 100
    """)
    dati = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('visualization_sensor.html', dati=dati)

@app.route('/visualization_station')
def visualization_station():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT nomestazione, nometiposensore, quota, lat, lng
        FROM stazioni_aria 
        ORDER BY nomestazione
        LIMIT 100
    """)
    dati = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('visualization_station.html', dati=dati)

@app.route('/aggiorna-dati-sensori', methods=['POST'])
def aggiorna_dati_sensori():
    update_last_30_data()
    return redirect(url_for('visualization_sensor'))

@app.route('/aggiorna-dati-stazioni', methods=['POST'])
def aggiorna_dati_stazioni():
    update_station_data()
    return redirect(url_for('visualization_station'))

@app.route('/elimina-ultimi-10-sensori', methods=['POST'])
def elimina_ultimi_10_sensori():
    elimina_ultimi_10_record()
    return redirect(url_for('visualization_sensor'))

@app.route('/elimina-ultimi-10-stazioni', methods=['POST'])
def elimina_ultimi_10_stazioni_route():
    elimina_ultimi_10_stazioni()  # Chiami la funzione importata dal modulo data_operations_station
    return redirect(url_for('visualization_station'))  # Redirect alla visualizzazione delle stazioni

if __name__ == '__main__':
    app.run(debug=True)

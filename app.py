from flask import Flask, render_template, redirect, url_for
from extractor import update_last_30_data
from data_operations import elimina_ultimi_10_record
from db import get_db_connection

app = Flask(__name__)

@app.route('/')
def index():
    return redirect(url_for('visualization'))

@app.route('/visualization')
def visualization():
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
    return render_template('visualization.html', dati=dati)

@app.route('/aggiorna-dati', methods=['POST'])
def aggiorna_dati():
    update_last_30_data()
    return redirect(url_for('visualization'))

@app.route('/elimina-ultimi-10', methods=['POST'])
def elimina_ultimi_10():
    elimina_ultimi_10_record()
    return redirect(url_for('visualization'))

if __name__ == '__main__':
    app.run(debug=True)



# air_quality_analysis/
#│
#├── app.py
#├── extractor.py
#├── data_operations.py
#├── db.py
#├── templates/
#│   └── visualization.html

# flask --app app run --debug 

from flask import Flask, render_template, request, redirect, url_for, flash
from functions import sensor_management

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Home page esistente
@app.route('/')
def home():
    return render_template('home.html')

# Dashboard sensori
@app.route('/sensor_dashboard')
def sensor_dashboard():
    status = sensor_management.sensor_count_records()
    dati = sensor_management.sensor_get_last_records(1000)  # ultimi 30 record
    return render_template("sensor_table.html", status=status, dati=dati)


@app.route('/sensor_create', methods=['POST'])
def sensor_create():
    sensor_management.sensor_create_table()
    flash("Tabella sensori creata con successo!")
    return redirect(url_for('sensor_dashboard'))

@app.route('/sensor_drop', methods=['POST'])
def sensor_drop():
    sensor_management.sensor_drop_table()
    flash("Tabella sensori eliminata con successo!")
    return redirect(url_for('sensor_dashboard'))

@app.route('/sensor_delete_n', methods=['POST'])
def sensor_delete_n():
    n = request.form.get('n', 10)
    try:
        sensor_management.sensor_delete_n_records(int(n))
        flash(f"Eliminati gli ultimi {n} record sensori.")
    except ValueError:
        flash("Numero non valido per l'eliminazione.")
    return redirect(url_for('sensor_dashboard'))

@app.route('/sensor_import_sample', methods=['POST'])
def sensor_import_sample():
    n = request.form.get('n', 100)
    try:
        sensor_management.sensor_import_sample_data(int(n))
        flash(f"Importato un campione di {n} dati sensori.")
    except ValueError:
        flash("Numero non valido per il campione.")
    return redirect(url_for('sensor_dashboard'))

@app.route('/sensor_update', methods=['POST'])
def sensor_update():
    sensor_management.sensor_update_data()
    flash("Aggiornati gli ultimi 30 dati sensori.")
    return redirect(url_for('sensor_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)

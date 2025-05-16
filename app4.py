from flask import Flask, render_template, request, redirect, flash
import psycopg2

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Necessary for flash messages

# Connessione al database
mydb = psycopg2.connect(
    host="localhost",
    database="se4gProject",
    user="se4g",
    password="admin"
)

c = mydb.cursor()

# Creare la tabella (se non esiste)
c.execute('''CREATE TABLE IF NOT EXISTS persons
             (id SERIAL PRIMARY KEY, 
             firstname TEXT, 
             lastname TEXT, 
             age INTEGER)''')

# Funzione per aggiungere una persona
def add_person(fname, lname, a):
    data = [fname, lname, a]
    c.execute("INSERT INTO persons(firstname, lastname, age) VALUES (%s, %s, %s)", data)

# Funzione per ottenere tutte le persone
def get_persons():
    c.execute('SELECT * FROM persons ORDER BY age')
    return c.fetchall()

# Funzione per ottenere una persona specifica
def get_person(fname):
    c.execute(f'SELECT * FROM persons WHERE firstname = %s', [fname])
    return c.fetchall()

@app.route('/')
def index():
    return render_template('index.html', persons=get_persons())

@app.route('/add', methods=['POST'])
def add():
    fname = request.form['firstname']
    lname = request.form['lastname']
    age = int(request.form['age'])
    add_person(fname, lname, age)
    mydb.commit()
    flash(f"Persona {fname} {lname} aggiunta con successo!")  # Flash message for success
    return redirect('/')

@app.route('/query', methods=['POST'])
def query():
    fname = request.form['firstname']
    
    # Se il campo 'firstname' è vuoto, mostra tutte le persone
    if not fname:
        persons = get_persons()
        flash("Tutti i dati sono stati mostrati.")  # Messaggio di feedback
    else:
        persons = get_person(fname)
        if not persons:
            flash(f"Nessuna persona trovata con il nome {fname}.")
    
    return render_template('index.html', persons=persons)


@app.route('/all')
def all_persons():
    return render_template('index.html', persons=get_persons())

if __name__ == '__main__':
    app.run(debug=True)

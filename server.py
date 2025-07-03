from flask import Flask, jsonify, request
import psycopg2
import pandas as pd
import warnings

from werkzeug.security import generate_password_hash, check_password_hash

# Filtro selettivo per il warning di pandas su psycopg2
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    message="pandas only supports SQLAlchemy connectable*"
)



app = Flask(__name__)

def db_connection():
    conn = psycopg2.connect(
        host="localhost",
        database="lombardia_air_quality",
        user="airdata_user",
        password="user"
    )
    return conn


def check_user_exists(username):
    conn = db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM users WHERE username = %s"
    cursor.execute(query, (username,))
    result = cursor.fetchone()
    cursor.close()
    return 1 if result else 0

# Login
@app.route('/api/login', methods=['POST'])
def login():
    conn = db_connection()
    data = request.get_json()
    username_or_email = data.get('username')
    password = data.get('password')

    if not username_or_email or not password:
        return jsonify({"message": "Username and password are required"}), 400

    cursor = conn.cursor()
    query = "SELECT username, email, password FROM users WHERE username = %s OR email = %s"
    cursor.execute(query, (username_or_email, username_or_email))
    user = cursor.fetchone()
    cursor.close()

    if not user:
        # Username/email not found
        return jsonify({"message": "Invalid username"}), 401

    stored_password = user[2]


    # Password verification in plain text
    if stored_password != password:
        return jsonify({"message": "Invalid password"}), 403
    
    # Password verification using hash (commented out)
    # if not check_password_hash(stored_password, password):
    #     return jsonify({"message": "Invalid password"}), 403


    return jsonify({"message": "Login successful"}), 200


@app.route('/api/signin', methods=['POST'])
def signin():
    conn = db_connection()
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({"message": "All fields are required"}), 400

    cursor = conn.cursor()
    query = "SELECT 1 FROM users WHERE username = %s OR email = %s"
    cursor.execute(query, (username, email))
    if cursor.fetchone():
        cursor.close()
        return jsonify({"message": "Username or email already exists"}), 409


    # Store password in plain text
    query = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)"
    cursor.execute(query, (username, email, password))

    # Password hashing for storage (commented out)
    # hashed_password = generate_password_hash(password)
    # query = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)"
    # cursor.execute(query, (username, email, hashed_password))


    conn.commit()
    cursor.close()

    return jsonify({"message": "Signup successful"}), 200



    
@app.route('/api/provinces', methods=['GET'])
def get_provinces():
    """
    Fetch distinct provinces from the database.
    This endpoint returns a list of distinct provinces from the station table sorted in alphabetical order.
    """
    try:
        conn = db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT provincia FROM station ORDER BY provincia")
        provinces = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return jsonify(provinces)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/stations', methods=['GET'])
def get_stations():
    pollutant = request.args.get('pollutant', default=None, type=str)  # load parameter
    
    try:
        conn = db_connection()
        
        if pollutant:
            query = """
                SELECT nomestazione, lat, lng, nometiposensore, idsensore, provincia
                FROM station
                WHERE lat IS NOT NULL AND lng IS NOT NULL
                AND nometiposensore = %s;
            """
            df = pd.read_sql_query(query, conn, params=(pollutant,))
        else:
            query = """
                SELECT nomestazione, lat, lng, nometiposensore, idsensore, provincia
                FROM station
                WHERE lat IS NOT NULL AND lng IS NOT NULL;
            """
            df = pd.read_sql_query(query, conn)
        
        conn.close()
        data = df.to_dict(orient='records')
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/api/measurements', methods=['GET'])
def get_measurements():
    idsensore = request.args.get('idsensore', default=None, type=str)

    try:
        conn = db_connection()

        base_query = "SELECT idsensore, data, valore, stato, idoperatore FROM measurement WHERE stato = 'VA' "
        params = []

        if idsensore:
            base_query += " AND idsensore = %s"
            params.append(idsensore)

        base_query += " ORDER BY data ASC"

        df = pd.read_sql_query(base_query, conn, params=tuple(params))
        conn.close()

        data = df.to_dict(orient='records')
        return jsonify(data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/api/measurements_filters', methods=['GET'])
def get_measurements_filters():
    # Get query parameters from URL
    provincia = request.args.get('provincia', type=str)
    pollutant = request.args.get('pollutant', type=str)
    start_date = request.args.get('start_date', type=str)
    end_date = request.args.get('end_date', type=str)


    try:
        conn = db_connection()
        params = []

        # Build SELECT and GROUP BY clauses dynamically depending on presence of 'provincia'
        if provincia:
            # Include province in SELECT and group by it
            select_clause = "SELECT m.data, AVG(m.valore) AS valore, s.provincia"
            group_by_clause = "GROUP BY m.data, s.provincia"
        else:
            # Exclude province if not specified in input
            select_clause = "SELECT m.data, AVG(m.valore) AS valore"
            group_by_clause = "GROUP BY m.data"

        # Base SQL query with JOIN between measurement and station
        base_query = f"""
            {select_clause}
            FROM measurement m
            JOIN station s ON m.idsensore = s.idsensore
            WHERE m.stato = 'VA'
        """

        # Add optional filters dynamically
        if provincia:
            base_query += " AND s.provincia = %s"
            params.append(provincia)

        if pollutant:
            base_query += " AND s.nometiposensore = %s"
            params.append(pollutant)

        if start_date:
            base_query += " AND m.data >= %s"
            params.append(start_date)

        if end_date:
            base_query += " AND m.data <= %s"
            params.append(end_date)

        # Finalize the query with GROUP BY and ORDER BY
        base_query += f" {group_by_clause} ORDER BY m.data"

        # Execute query and convert to JSON
        df = pd.read_sql_query(base_query, conn, params=params)
        conn.close()

        return jsonify(df.to_dict(orient='records'))

    except Exception as e:
        # Return error message in case of failure
        return jsonify({'error': str(e)}), 500



    

# Endpoint to get average pollutant values by province and time in map page   
@app.route('/api/avg_province_time', methods=['GET'])
def get_data_by_time():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    pollutant = request.args.get('pollutant', default='Ossidi di Azoto')

    try:
        conn = db_connection()
        if not start_date or not end_date:
            query = """
                SELECT s.unitamisura, s.provincia, AVG(m.valore) as mean
                FROM measurement as m JOIN station as s ON m.idsensore = s.idsensore
                WHERE s.nometiposensore = %s AND m.data >= (SELECT MAX(data) FROM measurement) - INTERVAL '7 days' 
                AND m.stato = 'VA'
                GROUP BY s.provincia, s.unitamisura;
                """
            df = pd.read_sql_query(query, conn, params=(pollutant,))    
        else:
            query = """
                SELECT s.unitamisura, s.provincia, AVG(m.valore) as mean
                FROM measurement as m JOIN station as s ON m.idsensore = s.idsensore
                WHERE s.nometiposensore = %s AND m.data >= %s AND m.data <= %s
                AND m.stato = 'VA'
                GROUP BY s.provincia, s.unitamisura;
            """
            df = pd.read_sql_query(query, conn, params=(pollutant, start_date, end_date))
        conn.close()
        return jsonify(df.to_dict(orient='records'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

if __name__ == '__main__':
    app.run(debug=True, port=5001)

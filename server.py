from flask import Flask, jsonify, request
import psycopg2
import pandas as pd
import warnings

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
    # query to retrieve user data
    sql_query = "SELECT * FROM users;"
    df_user = pd.read_sql_query(sql_query, conn)
    print('Dataframe:')
    print(df_user.head(), '\n') 

    #global df_user
    global logged_in
    logged_in = False
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # if the username or password is empty
    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400
    # if the username or email is incorrect
    elif username not in df_user['username'].values and username not in df_user['email'].values:
            return jsonify({"message": "Invalid username"}), 401
    # if the username is correct
    elif username in df_user['username'].values or username in df_user['email'].values:
        # check if the password is correct
        match = df_user[df_user['username'] == username]
        pw = match['password'].values[0]
        # if the password is incorrect
        if  pw != password:
            return jsonify({"message": "Invalid password"}), 403
        # if the password is correct
        else: 
            logged_in = True
            return jsonify({"message": "Login successful"}), 200
    else: 
        return jsonify({"message": "ERROR"}),500

# Signin
@app.route('/api/signin', methods=['POST'])
def signin():
    global logged_in
    conn = db_connection()
    new_data = request.get_json()
    username = new_data.get('username')
    email = new_data.get('email')
    password = new_data.get('password')
    # if the username or password or email is empty
    if not username or not password or not email:
        return jsonify({"message": "All fields are necessary to be registered"}), 400
    # if the username or email is already taken
    elif check_user_exists(username) == 1:
        return jsonify({"message": "Username already exists"}), 409
    else: 
        try:  
            cursor = conn.cursor()
            query = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)"
            cursor.execute(query, (username, email, password))
            conn.commit()
            logged_in = True
            return jsonify({"message": "Signin successful"}), 200
        except Exception as e:
            return jsonify({"message": f"Internal server error: {str(e)}"}), 500
        
    
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
    datainizio = request.args.get('datainizio', default=None, type=str)
    datafine = request.args.get('datafine', default=None, type=str)

    try:
        conn = db_connection()

        base_query = "SELECT idsensore, data, valore, stato, idoperatore FROM measurement WHERE stato = 'VA' "
        params = []

        if idsensore:
            base_query += " AND idsensore = %s"
            params.append(idsensore)

        if datainizio:
            base_query += " AND data >= %s"
            params.append(datainizio)

        if datafine:
            base_query += " AND data <= %s"
            params.append(datafine)

        base_query += " ORDER BY data ASC"

        df = pd.read_sql_query(base_query, conn, params=tuple(params))
        conn.close()

        data = df.to_dict(orient='records')
        return jsonify(data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/api/measurements2', methods=['GET'])
def api_get_measurements():
    pollutant_group = request.args.get('pollutant_group', type=str)
    province = request.args.get('province', type=str)
    start_date = request.args.get('start_date', type=str)
    end_date = request.args.get('end_date', type=str)

    try:
        conn = db_connection()
        query = """
            SELECT m.valore, s.nometiposensore, s.provincia, s.nomestazione, m.data
            FROM measurement m
            JOIN station s ON m.idsensore = s.idsensore
            WHERE m.valore IS NOT NULL AND s.lat IS NOT NULL AND s.lng IS NOT NULL
        """
        params = []

        if pollutant_group and pollutant_group != "All":
            if pollutant_group == "PM":
                query += " AND (s.nometiposensore LIKE 'PM%')"
            elif pollutant_group == "NOx":
                query += " AND (s.nometiposensore IN ('NO', 'NO2', 'NOx'))"
            elif pollutant_group == "Ozone":
                query += " AND s.nometiposensore = 'O3'"
            else:
                query += " AND s.nometiposensore = %s"
                params.append(pollutant_group)

        if province and province != "All":
            query += " AND s.provincia = %s"
            params.append(province)

        if start_date:
            query += " AND m.data >= %s"
            params.append(start_date)

        if end_date:
            query += " AND m.data <= %s"
            params.append(end_date)

        query += " ORDER BY m.data DESC LIMIT 10000"

        df = pd.read_sql_query(query, conn, params=params)
        conn.close()

        data = df.to_dict(orient='records')
        return jsonify(data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@app.route('/api/measurements_by_province', methods=['GET'])
def get_measurements_by_province():
    provincia = request.args.get('provincia', type=str)
    pollutant = request.args.get('pollutant', type=str)
    datainizio = request.args.get('datainizio', type=str)
    datafine = request.args.get('datafine', type=str)

    try:
        conn = db_connection()
        params = []
        
        base_query = """
            SELECT m.data, AVG(m.valore) AS valore, s.provincia
            FROM measurement m
            JOIN station s ON m.idsensore = s.idsensore
            WHERE m.stato = 'VA'
        """

        if provincia:
            base_query += " AND s.provincia = %s"
            params.append(provincia)
        
        if pollutant:
            base_query += " AND s.nometiposensore = %s"
            params.append(pollutant)
        
        if datainizio:
            base_query += " AND m.data >= %s"
            params.append(datainizio)
        
        if datafine:
            base_query += " AND m.data <= %s"
            params.append(datafine)

        base_query += " GROUP BY m.data, s.provincia ORDER BY m.data"

        df = pd.read_sql_query(base_query, conn, params=params)
        conn.close()

        return jsonify(df.to_dict(orient='records'))
    except Exception as e:
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
    app.run(debug=True, port=5000)

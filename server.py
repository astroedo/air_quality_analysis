from flask import Flask, jsonify, request
import psycopg2
import pandas as pd

# Ignore warnings from pandas about SQLAlchemy
import warnings
warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy")

app = Flask(__name__)

def db_connection():
    conn = psycopg2.connect(
        host="localhost",
        database="lombardia_air_quality",
        user="airdata_user",
        password="user"
    )
    return conn

@app.route('/api/stations', methods=['GET'])
def get_stations():
    pollutant = request.args.get('pollutant', default=None, type=str)  # load parameter
    
    try:
        conn = db_connection()
        
        if pollutant:
            query = """
                SELECT nomestazione, lat, lng, nometiposensore
                FROM station
                WHERE lat IS NOT NULL AND lng IS NOT NULL
                AND nometiposensore = %s;
            """
            df = pd.read_sql_query(query, conn, params=(pollutant,))
        else:
            query = """
                SELECT nomestazione, lat, lng, nometiposensore
                FROM station
                WHERE lat IS NOT NULL AND lng IS NOT NULL;
            """
            df = pd.read_sql_query(query, conn)
        
        conn.close()
        data = df.to_dict(orient='records')
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# --- LOGIN ---
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"message": "Username and password required"}), 400

    try:
        conn = db_connection()
        cur = conn.cursor()
        cur.execute("SELECT password FROM users WHERE username = %s", (username,))
        result = cur.fetchone()
        cur.close()
        conn.close()

        if not result:
            return jsonify({"message": "User not found"}), 401
        if result[0] != password:  # 🔐 Qui aggiungi controllo hash se vuoi
            return jsonify({"message": "Invalid password"}), 403

    except Exception as e:
        return jsonify({"message": f"Server error: {e}"}), 500

    return jsonify({"message": "Login successful", "username": username}), 200

# --- SIGNIN ---
@app.route('/api/signin', methods=['POST'])
def signin():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({"message": "All fields are required"}), 400

    try:
        conn = db_connection()
        cur = conn.cursor()

        cur.execute("SELECT 1 FROM users WHERE username = %s", (username,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({"message": "Username already exists"}), 409

        cur.execute("SELECT 1 FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({"message": "Email already registered"}), 409

        # 🔐 Qui salva la password criptata se vuoi
        cur.execute(
            "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
            (username, email, password)
        )
        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        return jsonify({"message": f"Server error: {e}"}), 500

    return jsonify({"message": "Signup successful", "username": username}), 200


""""
def check_user_exists(username):
    conn = db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM users WHERE username = %s"
    cursor.execute(query, (username,))
    result = cursor.fetchone()
    cursor.close()
    return 1 if result else 0

#LOGIN
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

#SIGNIN
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
"""


if __name__ == '__main__':
    app.run(debug=True, port=5000)

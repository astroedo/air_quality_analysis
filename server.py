from flask import Flask, jsonify, request, session
import psycopg2
import pandas as pd
import warnings

# Suppress pandas SQLAlchemy warning
warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy")

app = Flask(__name__)
app.secret_key = 'super-secret-key'  # Required to enable Flask session

# Database connection
def db_connection():
    return psycopg2.connect(
        host="localhost",
        database="lombardia_air_quality",
        user="airdata_user",
        password="user"
    )

# Protected API: only accessible by logged-in users
@app.route('/api/stations', methods=['GET'])
def get_stations():
    if 'username' not in session:
        return jsonify({'message': 'Unauthorized'}), 401

    pollutant = request.args.get('pollutant', default=None, type=str)

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
        return jsonify(df.to_dict(orient='records'))

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Login endpoint
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
        if result[0] != password:
            return jsonify({"message": "Invalid password"}), 403

        # Store user session
        session["username"] = username
        return jsonify({"message": "Login successful", "username": username}), 200

    except Exception as e:
        return jsonify({"message": f"Server error: {e}"}), 500

# Signup endpoint
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

        # Check if username or email already exists
        cur.execute("SELECT 1 FROM users WHERE username = %s", (username,))
        if cur.fetchone():
            return jsonify({"message": "Username already exists"}), 409

        cur.execute("SELECT 1 FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            return jsonify({"message": "Email already registered"}), 409

        # Insert new user
        cur.execute(
            "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
            (username, email, password)
        )
        conn.commit()
        cur.close()
        conn.close()

        # Automatically log in new user
        session["username"] = username
        return jsonify({"message": "Signup successful", "username": username}), 200

    except Exception as e:
        return jsonify({"message": f"Server error: {e}"}), 500

# Logout endpoint
@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop("username", None)
    return jsonify({"message": "Logged out"}), 200

# Return current logged-in user
@app.route('/api/me', methods=['GET'])
def get_current_user():
    if "username" in session:
        return jsonify({"username": session["username"]}), 200
    return jsonify({"message": "Not logged in"}), 401



# Run server
if __name__ == '__main__':
    app.run(debug=True, port=5000)

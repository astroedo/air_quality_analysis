from flask import Flask, jsonify, request, session
import psycopg2
import pandas as pd
import jwt
import datetime
from functools import wraps
import bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'questa_è_una_chiave_segretissima'  # change it!

# Database connection
def db_connection():
    return psycopg2.connect(
        host="localhost",
        database="lombardia_air_quality",
        user="airdata_user",
        password="user"
    )



# Decorator to protect routes with JWT token
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Token passato nell'header Authorization
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]  # Bearer <token>
        if not token:
            return jsonify({'message': 'Token mancante!'}), 401
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = data['username']
        except:
            return jsonify({'message': 'Token non valido!'}), 401

        return f(current_user, *args, **kwargs)
    return decorated



## -- ACCOUNT API --

# User registration endpoint
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not all([username, email, password]):
        return jsonify({"message": "Missing required fields"}), 400

    # Hash the password before storing it
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    try:
        conn = db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (username, email, password)
            VALUES (%s, %s, %s)
        """, (username, email, hashed_pw))
        conn.commit()
        return jsonify({"message": "User registered successfully"}), 201
    except psycopg2.IntegrityError:
        conn.rollback()
        return jsonify({"message": "Username or email already exists"}), 409
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# User login endpoint
@app.route('/api/login', methods=['POST'])
def login():
    auth = request.json
    if not auth or not auth.get('username') or not auth.get('password'):
        return jsonify({'message': 'Username e password richiesti'}), 400
    
    username = auth['username']
    password = auth['password']

    try:
        conn = db_connection()
        cur = conn.cursor()
        cur.execute("SELECT password FROM users WHERE username = %s", (username,))
        row = cur.fetchone()
        conn.close()

        if not row:
            return jsonify({'message': 'User not found'}), 401

        hashed_pw = row[0]

        if not bcrypt.checkpw(password.encode('utf-8'), hashed_pw.encode('utf-8')):
            return jsonify({'message': 'Incorrect password'}), 401

        token = jwt.encode({
            'username': username,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
        }, app.config['SECRET_KEY'], algorithm="HS256")

        return jsonify({'token': token})  
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# User profile endpoint
@app.route('/api/profile', methods=['GET'])
@token_required
def profile(current_user):
    try:
        conn = db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT username, email, type, created_at
            FROM users
            WHERE username = %s
        """, (current_user,))
        user = cur.fetchone()
        conn.close()

        if not user:
            return jsonify({'message': 'User not found'}), 404

        user_data = {
            'username': user[0],
            'email': user[1],
            'type': user[2],
            'created_at': user[3].isoformat()
        }

        return jsonify(user_data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


## -- APP API --

# Station
@app.route('/api/stations', methods=['GET'])
# @token_required       # Uncomment this line to protect the endpoint with JWT
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)

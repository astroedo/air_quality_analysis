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

    


if __name__ == '__main__':
    app.run(debug=True, port=5000)

from flask import Flask, jsonify, request
import json

# login /signin 
app = Flask("GeoAir")

def signin():
    print('For signin insert your data:\n')
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    # put the data into USER DATABASE, simulate saving to a database
    with open('users.json', 'a') as f: # to be defined !!!!!
        json.dump({"username": username, "email": email, "password": password}, f)
        f.write('\n')
    if not username or not password or not email:
        return jsonify({"message": "Username and password are required"}), 400
    else:       
        return jsonify({"message": "Signin successful"}), 200










# start the Flask server
app.run(port=5000)
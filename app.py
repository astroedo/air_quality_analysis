# flask --app app run --debug 

from flask import Flask, render_template, request, redirect, url_for, flash
from functions import sensor_management

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Home page esistente
@app.route('/')
def home():
    return 


if __name__ == '__main__':
    app.run(debug=True)

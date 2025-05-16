from flask import Flask
from markupsafe import Markup  # Correct import for Markup
from markupsafe import escape

app = Flask(__name__)

@app.route('/')
def index():
    return 'Index Page'

@app.route('/user/<username>')
def show_user_profile(username):
    # show the user profile for that user
    # http://127.0.0.1:5000/user/Gian -> User Gian
    return f'User {escape(username)}'

@app.route('/number/<int:num>')
def show_number(num):
    # show the post with the given id, the id is an integer
    # http://127.0.0.1:5000/number/5 -> My number is 5
    return f'My number is {num}'

@app.route('/path/<path:subpath>')
def show_subpath(subpath):
    # show the subpath after /path/
    # http://127.0.0.1:5000/path/air/quality -> Subpath air/quality
    return f'Subpath {escape(subpath)}'



# show all routes
@app.route('/allRoutes')
def all_routes():
    output = "<h2>All Routes</h2><pre>"

    for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
        methods = ', '.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        line = f"{rule.rule:30s} -> {rule.endpoint:20s} [{methods}]"
        output += line + "\n"

    output += "</pre>"
    return Markup(output)

if __name__ == '__main__':
    app.run(debug=True)

    
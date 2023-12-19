from flask import Flask, request, render_template, g
from flask_restful import Resource, Api, reqparse
import sqlite3
import os

app = Flask(__name__)
api = Api(app)

# SQLite database in-memory (for simplicity in this example)
DATABASE = '/app/data.db'  # Store the database in a file

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.before_request
def before_request():
    g.db = get_db()

@app.route('/')
def index():
    cur = g.db.execute('SELECT id, name FROM users')
    users = cur.fetchall()
    return render_template('index.html', users=users)

# RESTful API endpoint for getting user data
class UserResource(Resource):
    def get(self, user_id=None):
        if user_id is None:
            cur = g.db.execute('SELECT id, name FROM users')
            users = cur.fetchall()
            return {'users': [{'id': user['id'], 'name': user['name']} for user in users]}
        else:
            cur = g.db.execute('SELECT id, name FROM users WHERE id = ?', (user_id,))
            user = cur.fetchone()
            if user is None:
                return {'error': 'User not found'}, 404
            return {'user': {'id': user['id'], 'name': user['name']}}

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, required=True, help='Name cannot be blank')
        args = parser.parse_args()

        cur = g.db.execute('INSERT INTO users (name) VALUES (?)', (args['name'],))
        g.db.commit()

        return {'message': 'User created successfully', 'user': {'id': cur.lastrowid, 'name': args['name']}}, 201

api.add_resource(UserResource, '/api/users', '/api/users/<int:user_id>')

if __name__ == '__main__':
    # Check if the database file exists, if not, initialize the database
    if not os.path.exists(DATABASE):
        init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)

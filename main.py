from flask import Flask, jsonify, render_template, request
import sqlite3, hashlib
from datetime import datetime

app = Flask(__name__)

DATABASE = 'database/database.db'

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('database/schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.route('/')
def index():
    return render_template('index.html', name='index')

@app.route('/login')
def login():
    return render_template('login.html', name='login')

@app.route('/cadastro')
def cadastro():
    return render_template('cadastro.html', name='cadastro')

@app.route('/excluir')
def excluir():
    return render_template('excluir.html', name='excluir')

@app.route('/initdb')
def initialize_database():
    init_db()
    return 'Base de Dados Inicializada!'

@app.route('/users', methods=['POST'])
def post_user():
    login = request.json.get('login')
    password = request.json.get('password')
    name = request.json.get('name')
    status = True
    createdAt = datetime.now()
    updatedAt = datetime.now()

    if not login:
        return jsonify({'error': 'login: most not be null!'})
    if not password:
        return jsonify({'error': 'password: most not be null!'})
    if not name:
        return jsonify({'error': 'name: most not be null!'})

    if not isinstance(login, str):
        return jsonify({'error': 'login: must be alphanumeric!'})

    if not isinstance(password, str):
        return jsonify({'error': 'password: must be alphanumeric!'})

    if not isinstance(name, str):
        return jsonify({'name': 'name: must be alphanumeric!'})

    if '@' not in login:
        return jsonify({'error': 'login: insert a valid e-mail!'})

    if len(password) < 8:
        return jsonify({'error': 'password: enter at least 8 characters!'})

    loginIsValid = valid_use_user(login)

    if not loginIsValid:
        return jsonify({'error': 'Login already used!'}), 400

    hashedPassword = hashlib.sha256(password.encode()).hexdigest()

    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('INSERT INTO users (login, password, name, status, createdAt, updatedAt) VALUES (?, ?, ?, ?, ?, ?)', (login, hashedPassword, name, status, createdAt, updatedAt))
        db.commit()
        return jsonify({'message': 'User created!'})
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/users', methods=['GET'])
def get_users():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users')
        dados = cursor.fetchall()
        return jsonify([dict(row) for row in dados])
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?',(user_id,))
        user = cursor.fetchone()
        if user:
            return jsonify(dict(user))
        else:
            return jsonify({'error': 'User not found!'})
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('DELETE FROM users WHERE id = ?',(user_id,))
        db.commit()
        return jsonify({'message': 'User deleted!'})
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/users/changeStatus/<int:user_id>', methods=['PATCH'])
def patch_user(user_id):

    status = request.json.get('status')

    if status == None:
        return jsonify({'error': 'status: most not be null!'})

    if not isinstance(status, bool):
        return jsonify({'error': 'password: must be boolean!'})

    updatedAt = datetime.now()

    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('UPDATE users set status = ?, updatedAt = ? WHERE id = ?', (status, updatedAt, user_id,))
        db.commit()
        return jsonify({'message': 'User updated!'})
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

def valid_use_user(login):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users WHERE login = ?',(login,))
        user = cursor.fetchone()
        if user:
            return False
        else:
            return True
    finally:
        db.close()

if __name__ == '__main__':
    app.run(debug=True)

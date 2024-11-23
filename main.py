from flask import Flask, jsonify, render_template, request, redirect, url_for, flash
import sqlite3, hashlib
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from datetime import datetime

app = Flask(__name__)

DATABASE = 'database/database.db'

app.secret_key = 'your_secret_key'

# Configuração do servidor de e-mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'joaoocolombo@gmail.com'
app.config['MAIL_PASSWORD'] = ''
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

mail = Mail(app)

# Serializador para gerar os tokens seguros
s = URLSafeTimedSerializer(app.secret_key)

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

@app.route('/loginUsuario', methods=['GET'])
def loginUsuario():
    login = request.args.get('login')
    password = request.args.get('password')

    returnTemplate = redirect(url_for('login'))

    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users WHERE login = ?', (login,))
        user = cursor.fetchone()
        if user:

            status = user[4]

            if not status:
                flash('User is blocked!', 'danger')
                return returnTemplate

            hashedPassword = user[2]

            if hashedPassword != hashlib.sha256(password.encode()).hexdigest():
                flash('Invalid password!', 'danger')
                return returnTemplate
        else:
            flash('User not found!', 'danger')
            return returnTemplate
    except sqlite3.Error as e:
        flash(str(e), 'danger')
        return returnTemplate
    finally:
        db.close()
        if user:
            return redirect(url_for('index'))
        return returnTemplate

@app.route('/cadastro')
def cadastro():
    return render_template('cadastro.html', name='cadastro')
@app.route('/cadastroUsuario', methods=['POST'])
def cadastroUsuario():
    name = request.form.get('name')
    login = request.form.get('login')
    password = request.form.get('password')

    status = True
    createdAt = datetime.now()
    updatedAt = datetime.now()

    returnTemplate = redirect(url_for('cadastro'))

    if len(password) < 8:
        flash('Password: enter at least 8 characters!', 'danger')
        return returnTemplate

    loginIsValid = valid_use_user(login)

    if not loginIsValid:
        flash('Login already used!', 'danger')
        return returnTemplate

    hashedPassword = hashlib.sha256(password.encode()).hexdigest()

    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            'INSERT INTO users (login, password, name, status, createdAt, updatedAt) VALUES (?, ?, ?, ?, ?, ?)',
            (login, hashedPassword, name, status, createdAt, updatedAt))
        db.commit()
        flash('Registration completed successfully!', 'success')
        return returnTemplate
    except sqlite3.Error as e:
        flash(str(e), 'success')
        return returnTemplate
    finally:
        db.close()
        return returnTemplate

@app.route('/excluir')
def excluir():
    return render_template('excluir.html', name='excluir')

@app.route('/excluirUsuario', methods=['GET'])
def excluirUsuario():
    login = request.args.get('login')
    status = False
    updatedAt = datetime.now()

    returnTemplate = redirect(url_for('excluir'))

    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('UPDATE users set status = ?, updatedAt = ? WHERE login = ?', (status, updatedAt, login,))
        db.commit()
        flash('User deleted successfully!', 'success')
        return returnTemplate
    except sqlite3.Error as e:
        flash(str(e), 'success')
        return returnTemplate
    finally:
        db.close()
        return returnTemplate

@app.route('/atualizar')
def atualizar():
    return render_template('atualizar.html', name='atualizar')

@app.route('/atualizarUsuario', methods=['GET'])
def atualizarUsuario():
    name = request.args.get('name')
    login = request.args.get('login')
    password = request.args.get('password')
    updatedAt = datetime.now()

    hashedPassword = hashlib.sha256(password.encode()).hexdigest()

    returnTemplate = redirect(url_for('atualizar'))

    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('UPDATE users set name = ?, password = ? ,updatedAt = ? WHERE login = ?', (name, hashedPassword, updatedAt, login,))
        db.commit()
        flash('User updated successfully!', 'success')
        return returnTemplate
    except sqlite3.Error as e:
        flash(str(e), 'success')
        return returnTemplate
    finally:
        db.close()
        return returnTemplate

@app.route('/registros')
def registros():
    # Parâmetros de paginação
    page = request.args.get('page', 1, type=int)
    per_page = 2  # Número de registros por página
    offset = (page - 1) * per_page

    # Conectar ao banco de dados e buscar os registros com base na página e no limite
    db = get_db()
    cursor = db.cursor()
    # Consultar o total de registros
    cursor.execute("SELECT COUNT(*) AS total FROM users")
    total_records = cursor.fetchone()['total']

    # Consultar registros específicos para a página atual
    cursor.execute("SELECT * FROM users LIMIT ? OFFSET ?", (per_page, offset))
    registros = cursor.fetchall()

    db.close()

    # Calcular o total de páginas
    total_pages = (total_records + per_page - 1) // per_page

    return render_template('registros.html', registros=registros, page=page, total_pages=total_pages)

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

# Rota para solicitar redefinição de senha
@app.route('/esqueceu_senha', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('login')
        try:
            db = get_db()
            cursor = db.cursor()
            cursor.execute('SELECT * FROM users WHERE login = ?', (email,))
            user = cursor.fetchone()
            if user:
                # preparação e envio do email
                token = s.dumps(email, salt='password_recovery')
                msg = Message('Redefinição de Senha', sender='joaoocolombo@gmail.com', recipients=[email])

                link = url_for('reset_password', token=token, _external=True)
                msg.body = f'Clique no link para redefinir a sua senha! {link}'
                mail.send(msg)

                flash('Um link de recuperação de senha foi enviado para o seu email', category='success')

                return redirect(url_for('index'))
            else:
                return flash('User not found!', 'danger')
        except sqlite3.Error as e:
            return flash('error' ,'danger')
        finally:
            return render_template('esqueceu_senha.html')

    return render_template('esqueceu_senha.html')

# Rota para redefinir a senha
@app.route('/alterar_senha/<token>', methods=['GET', 'POST'])
def reset_password(token):

    try:
        login = s.loads(token, salt='password_recovery', max_age=3600) # 1h
    except SignatureExpired:
        return '<h1> O link de redefinição de senha expirou</h1>'
    except BadSignature:
        return '<h1>Token inválido</h1>'
    if request.method == 'POST':

        password = request.form.get('password')
        password2 = request.form.get('password2')

        if password != password2:
            flash('As senhas precisam ser iguais!', 'danger')
            return render_template('alterar_senha.html', token=token)

        updatedAt = datetime.now()
        hashedPassword = hashlib.sha256(password.encode()).hexdigest()

        try:
            db = get_db()
            cursor = db.cursor()
            cursor.execute('UPDATE users set password = ? ,updatedAt = ? WHERE login = ?',
                           (hashedPassword, updatedAt, login,))
            db.commit()
            flash('Sua senha foi redefinida com sucesso!', category='success')
            return redirect(url_for('index'))
        except sqlite3.Error as e:
            return flash('error', 'danger')
        finally:
            return redirect(url_for('index'))

    return render_template('alterar_senha.html', token=token)

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

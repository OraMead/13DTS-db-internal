from flask import Flask, render_template, request, redirect, session
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt

DB_name = 'notes.db'

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = 'aiurghrbuinwtugabdbwtr'


def create_connection(db_file):
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)
        print('Error while connecting to database')
        return None


def is_logged_in():
    if session.get('email') is None:
        return False
    else:
        return True


def insert(query: str, data: tuple, redirect_loc: str = None):
    con = create_connection(DB_name)
    cur = con.cursor()
    try:
        cur.execute(query, data)
    except sqlite3.IntegrityError:
        print('DB insert error')
        return redirect(redirect_loc) if redirect else None
    con.commit()
    con.close()


def fetch(query: str, arguments: tuple=()):
    con = create_connection(DB_name)
    cur = con.cursor()
    cur.execute(query, arguments)
    data = cur.fetchall()
    con.close()

    return data


@app.route('/')
def render_home():
    return render_template('index.html', title='home', logged_in=is_logged_in())


@app.route('/about')
def render_about():
    return render_template('about.html', title='about', logged_in=is_logged_in())


@app.route('/dashboard')
def render_dashboard():
    if not is_logged_in():
        return redirect('/')
    
    notes_list = fetch('SELECT note.title, note.content, subject.name '
    'FROM note JOIN subject ON note.fk_subject_id = subject.subject_id WHERE note.fk_user_id=?', 
    (session['userid'], ))

    for i, note in enumerate(notes_list):
        file_path = f"user_data/{session['userid']}/notes/{note[1]}"
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        notes_list[i] = (note[0], content[:150] + '...', note[2])


    return render_template('dashboard.html', title='dashboard', logged_in=is_logged_in(), notes=notes_list)


@app.route('/login', methods=['GET', 'POST'])
def render_login():
    if is_logged_in():
        return redirect('/')
    if request.method == 'POST':
        email = request.form.get('email').strip().lower()
        password = request.form.get('password')

        user_data = fetch('SELECT user_id, fname, lname, password, role FROM user WHERE email = ?', (email,))

        try:
            userid = user_data[0][0]
            firstname = user_data[0][1]
            lastname = user_data[0][2]
            db_password = user_data[0][3]
            role = user_data[0][4]
        except IndexError:
            return redirect('/login?error=email+and+or+password+invalid')
        
        if not bcrypt.check_password_hash(db_password, password):
            return redirect('/login?error=email+and+or+password+invalid')
        
        session['email'] = email
        session['userid'] = userid
        session['firstname'] = firstname
        session['lastname'] = lastname
        session['role'] = role
        return redirect('/')

    return render_template('login.html', title='login', logged_in=is_logged_in())


@app.route('/signup', methods=['GET', 'POST'])
def render_signup_page():
    if is_logged_in():
        return redirect('/')
    if request.method == 'POST':
        fname = request.form.get('fname').strip().title()
        lname = request.form.get('lname').strip().title()
        email = request.form.get('email').strip().lower()
        password = request.form.get('password')
        password2 = request.form.get('password2')
        role = request.form.get('role')

        if password != password2:
            return redirect('/signup?error=passwords+dont+match')
        
        if len(password) < 8:
            return redirect('/signup?error=password+too+short')

        hashed_password = bcrypt.generate_password_hash(password)

        insert('INSERT INTO user(user_id, fname, lname, email, password, role) VALUES(NULL,?,?,?,?,?)',
                (fname, lname, email, hashed_password, role),
                '/signup?error=invalid+email')

        return redirect('/login')

    return render_template('signup.html', title='signup', logged_in=is_logged_in())


@app.route('/logout')
def logout():
    [session.pop(key) for key in list(session.keys())]
    return redirect('/login')


@app.route('/account')
def render_account():
    if not is_logged_in():
        return redirect('/')
    user_list = fetch('SELECT fname, lname FROM user WHERE user_id=?;', (session['userid'], ))

    return render_template('account.html', title='account', logged_in=is_logged_in())


if __name__ == '__main__':
    app.run()

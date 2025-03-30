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


@app.route('/tutorial/')
def render_tutorials():
    tutorial_list = fetch('''SELECT subject.name, tutorial.level, tutorial.time, tutorial.location, user.fname, user.lname, tutorial.tutorial_id, tutorial.day
                            FROM ((tutorial
                            JOIN user ON tutorial.fk_tutor_id = user.user_id)
                            JOIN subject ON tutorial.fk_subject_id = subject.subject_id)
                            WHERE tutorial.fk_tutee_id IS NULL
                            ORDER BY subject.name, tutorial.day, tutorial.time''')

    return render_template('tutorial.html', title='tutorials', logged_in=is_logged_in(), tutorials=tutorial_list)


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


@app.route('/create', methods=['GET', 'POST'])
def render_create():
    if not is_logged_in():
        return redirect('/account?error=not+logged+in')
    if session['tutor'] != 1:
        return redirect('/account?error=not+tutor')
    
    subject_list = fetch('SELECT subject_id, name FROM subject')

    if request.method == 'POST':
        subject = request.form.get('subject')
        location = request.form.get('location').strip()
        time = request.form.get('time')
        description = request.form.get('description')
        level = request.form.get('level')
        day = request.form.get('day')

        insert('''INSERT INTO tutorial(tutorial_id, fk_subject_id, fk_tutor_id, location, time, fk_tutor_id, description, level, day)
               VALUES(NULL,?,?,?,?,NULL,?,?,?)''',
               (subject, session['userid'], location, time, description, level, day),
               '/create?error=failed+creating+session')

        return redirect('/account')
    
    return render_template('create.html', title='create', logged_in=is_logged_in(), subjects=subject_list)
    
    


@app.route('/logout')
def logout():
    [session.pop(key) for key in list(session.keys())]
    return redirect('/login')


@app.route('/account')
def render_account():
    if not is_logged_in():
        return redirect('/')
    booking_list = fetch('''SELECT subject.name, tutorial.level, tutorial.time, tutorial.location, user.fname, user.lname, tutorial.tutorial_id, tutorial.day
                            FROM ((tutorial
                            JOIN user ON tutorial.fk_tutor_id = user.user_id)
                            JOIN subject ON tutorial.fk_subject_id = subject.subject_id)
                            WHERE tutorial.fk_tutee_id=?
                            ORDER BY tutorial.day, tutorial.time;''',
                            (session['userid'], ))
    if session['tutor'] == 1:
        class_list = fetch('''SELECT subject.name, tutorial.level, tutorial.time, tutorial.location, user.fname, user.lname, tutorial.tutorial_id, tutorial.day
                            FROM ((tutorial
                            JOIN subject ON tutorial.fk_subject_id = subject.subject_id)
                            LEFT JOIN user ON tutorial.fk_tutee_id = user.user_id)
                            WHERE tutorial.fk_tutor_id=?
                            ORDER BY tutorial.day, tutorial.time;''',
                            (session['userid'], ))
    else:
        class_list = None

    return render_template('account.html', title='account', logged_in=is_logged_in(), bookings=booking_list, classes=class_list)


@app.route('/detail/<tutorial_id>')
def render_detail(tutorial_id):
    detail_list = fetch('''SELECT subject.name, tutorial.description, tutorial.level, tutorial.time, tutorial.location, user.fname, user.lname, tutorial.tutorial_id, tutorial.fk_tutor_id, tutorial.fk_tutee_id, tutorial.day
                            FROM ((tutorial
                            JOIN user ON tutorial.fk_tutor_id = user.user_id)
                            JOIN subject ON tutorial.fk_subject_id = subject.subject_id)
                            WHERE tutorial.tutorial_id=?''',
                            (tutorial_id, ))
    
    if detail_list[0][9] is not None:
        try:
            if session['userid'] != detail_list[0][8] and session['userid'] != detail_list[0][9]:
                return redirect('/tutorial?error=invalid+account')
        except IndexError:
            return redirect('/tutorial?error=not+logged+in')

    return render_template('detail.html', title='detail', logged_in=is_logged_in(), detail=detail_list)


@app.route('/book/<tutorial_id>')
def book(tutorial_id):
    detail_list = fetch('SELECT fk_tutor_id, fk_tutee_id FROM tutorial WHERE tutorial_id=?;', (tutorial_id, ))
    if not is_logged_in():
        return redirect(f'/detail/{tutorial_id}?error=not+logged+in')
    if detail_list[0][1] is not None:
        return redirect(f'/detail/{tutorial_id}?error=tutorial+already+booked')
    if detail_list[0][0] == session['userid']:
        return redirect(f'/detail/{tutorial_id}?error=user+is+tutor')
    
    insert('UPDATE tutorial SET fk_tutee_id=? WHERE tutorial_id=?;', (session['userid'], tutorial_id))

    return redirect('/account')


@app.route('/cancel/<tutorial_id>')
def cancel(tutorial_id):
    detail_list = fetch('SELECT fk_tutor_id, fk_tutee_id FROM tutorial WHERE tutorial_id=?;', (tutorial_id, ))
    if not is_logged_in():
        return redirect(f'/detail/{tutorial_id}?error=not+logged+in')
    if detail_list[0][1] is None:
        return redirect(f'/detail/{tutorial_id}?error=tutorial+not+booked')
    if detail_list[0][0] == session['userid']:
        return redirect(f'/detail/{tutorial_id}?error=user+is+tutor')
    
    insert('UPDATE tutorial SET fk_tutee_id=null WHERE tutorial_id=?;', (tutorial_id, ))

    return redirect('/account')


@app.route('/delete/<tutorial_id>')
def delete(tutorial_id):
    detail_list = fetch('SELECT fk_tutor_id, fk_tutee_id FROM tutorial WHERE tutorial_id=?;', (tutorial_id, ))
    if not is_logged_in():
        return redirect(f'/detail/{tutorial_id}?error=not+logged+in')
    if detail_list[0][1] is not None:
        return redirect(f'/detail/{tutorial_id}?error=tutorial+booked')
    if detail_list[0][0] != session['userid']:
        return redirect(f'/detail/{tutorial_id}?error=user+is+not+tutor')
    
    insert('DELETE FROM tutorial WHERE tutorial_id=?;', (tutorial_id, ))

    return redirect('/account')


if __name__ == '__main__':
    app.run()

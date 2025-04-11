from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt
import os

DB_PATH = 'notes.db'

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = 'aiurghrbuinwtugabdbwtr'

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def get_note_content(note_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM note WHERE note_id = ?", (note_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        filepath = f'uploads/{result[0]}'
        if os.path.exists(filepath):
            with open(filepath, 'r') as file:
                content = file.read()
            return filepath, content
    return None, None


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
    con = create_connection(DB_PATH)
    cur = con.cursor()
    try:
        cur.execute(query, data)
    except sqlite3.IntegrityError:
        print('DB insert error')
        return redirect(redirect_loc) if redirect else None
    con.commit()
    con.close()


def fetch(query: str, arguments: tuple=()):
    con = create_connection(DB_PATH)
    cur = con.cursor()
    cur.execute(query, arguments)
    data = cur.fetchall()
    con.close()

    return data


def process_note(note):
    file_path = f'uploads/{note[2]}'
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        content = ''
    
    truncated_content = content[:150] + '...' if len(content) > 150 else content

    try:
        tags = list(note[4].split('|'))
        for i, tag in enumerate(tags):
            tags[i] = tuple(tag.split(':'))
    except AttributeError:
        tags = ()
    
    try:
        return (note[0], note[1], truncated_content, note[3], tags, note[5])
    except:
        return (note[0], note[1], truncated_content, note[3], tags)


@app.route('/')
def index():
    return render_template('index.html', title='home', logged_in=is_logged_in())


@app.route('/about')
def about():
    return render_template('about.html', title='about', logged_in=is_logged_in())


@app.route('/dashboard')
def dashboard():
    if not is_logged_in():
        return redirect('/')
    
    note_list = fetch('''SELECT 
                            n.note_id,
                            n.title,
                            n.content,
                            s.name,
                            GROUP_CONCAT(t.tag_id || ':' || t.name, '|') AS tags
                       FROM note n
                       JOIN subject s ON n.fk_subject_id = s.subject_id
                       LEFT JOIN note_tag nt ON n.note_id = nt.fk_note_id
                       LEFT JOIN tag t ON nt.fk_tag_id = t.tag_id
                       WHERE n.fk_user_id = ?
                       GROUP BY n.note_id, n.title, n.content, s.name
                       ORDER BY n.updated_at DESC;''', 
                       (session['userid'], ))
    shared_list = fetch('''SELECT
                            n.note_id,
                            n.title,
                            n.content,
                            s.name,
                            GROUP_CONCAT(t.tag_id || ':' || t.name, '|') AS tags,
                            u.fname || ' ' || u.lname AS owner
                        FROM note n
                        JOIN subject s ON n.fk_subject_id = s.subject_id
                        LEFT JOIN note_tag nt ON n.note_id = nt.fk_note_id
                        LEFT JOIN tag t ON nt.fk_tag_id = t.tag_id
                        JOIN user u ON n.fk_user_id = u.user_id
                        JOIN shared_note sn ON n.note_id = sn .fk_note_id
                        WHERE sn.fk_user_id = ?
                        GROUP BY n.note_id, n.title, s.name, n.content
                        ORDER BY n.updated_at DESC;''', 
                       (session['userid'], ))
    subject_list = fetch('SELECT subject_id, name FROM subject WHERE fk_user_id=?', (session['userid'], ))
    tag_list = fetch('SELECT tag_id, name FROM tag WHERE fk_user_id IS NULL OR fk_user_id=?', (session['userid'], ))

    for i, note in enumerate(note_list):
        note_list[i] = process_note(note)
    
    for i, note in enumerate(shared_list):
        shared_list[i] = process_note(note)

    return render_template('dashboard.html', title='dashboard', logged_in=is_logged_in(), notes=note_list, shared=shared_list, subjects=subject_list, tags=tag_list)


@app.route('/login', methods=['GET', 'POST'])
def login():
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
def signup():
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
def account():
    if not is_logged_in():
        return redirect('/')
    user_list = fetch('SELECT fname, lname FROM user WHERE user_id=?;', (session['userid'], ))

    return render_template('account.html', title='account', logged_in=is_logged_in())


@app.route('/upload', methods=['POST'])
def upload():
    title = request.form.get('title', '').strip() or 'Untitled Note'
    file = request.files.get('file')
    subject = request.form.get('subject')
    new_subject = request.form.get('new-subject').strip()

    if file and not allowed_file(file.filename):
        return "Invalid file type", 400

    con = create_connection(DB_PATH)
    cur = con.cursor()

    if subject == 'add-new' and new_subject:
        cur.execute('INSERT INTO subject (fk_user_id, name) VALUES (?, ?)', (session['userid'], new_subject))
        subject = cur.lastrowid

    cur.execute('INSERT INTO note (fk_user_id, fk_subject_id, title, type) VALUES (?, ?, ?, 0)', (session['userid'], subject, title))
    note_id = cur.lastrowid

    new_filename = f"file_{note_id}.txt"

    if file and file.filename and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        new_filename = f"file_{note_id}.{ext}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
    else:
        new_filename = f"file_{note_id}.txt"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('')

    cur.execute('UPDATE note SET content = ? WHERE note_id = ?', (new_filename, note_id))
    con.commit()
    con.close()
    
    return redirect('/dashboard')


@app.route('/edit/<int:note_id>', methods=['GET', 'POST'])
def edit_note(note_id):
    if request.method == 'POST':
        content = request.form['content']
        filepath = request.form['filepath']
        with open(filepath, 'w') as file:
            file.write(content)
        insert('UPDATE note set updated_at = CURRENT_TIMESTAMP WHERE note_id = ?', (note_id, ))
        return redirect(url_for('index'))

    filepath, content = get_note_content(note_id)
    if filepath:
        return render_template('editor.html', title='Editor', content=content, filepath=filepath, note_id=note_id)
    return "File not found", 404


@app.route('/tag/<int:note_id>', methods=['POST'])
def edit_tags(note_id):
    return f'test {note_id}'


if __name__ == '__main__':
    app.run(debug=True)

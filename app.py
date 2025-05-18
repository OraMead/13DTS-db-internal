from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import sqlite3
from flask_bcrypt import Bcrypt
import os
import shutil

DB_PATH = 'notes.db'

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = 'aiurghrbuinwtugabdbwtr'

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt'}
ADMIN_PASSWORD = 'ADMINPASSWORD'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

NOTE_LIST_QUERY = '''SELECT 
                        n.note_id,
                        n.title,
                        s.name,
                        n.fk_subject_id,
                        (
                            SELECT GROUP_CONCAT(t.tag_id || ':' || t.name, '|')
                            FROM note_tag nt
                            JOIN tag t ON nt.fk_tag_id = t.tag_id
                            WHERE nt.fk_note_id = n.note_id
                        ) AS tags,
                        (
                            SELECT GROUP_CONCAT(u.user_id || ':' || u.fname || ' ' || u.lname || ':' || sn.permission, '|')
                            FROM shared_note sn
                            JOIN user u ON sn.fk_user_id = u.user_id
                            WHERE sn.fk_note_id = n.note_id
                        ) AS shared
                    FROM note n
                    JOIN subject s ON n.fk_subject_id = s.subject_id
                    WHERE n.fk_user_id = ?
                    ORDER BY n.updated_at DESC;'''
SHARED_LIST_QUERY = '''SELECT 
                            n.note_id,
                            n.title,
                            s.name,
                            n.fk_subject_id,
                            (
                                SELECT GROUP_CONCAT(t.tag_id || ':' || t.name, '|')
                                FROM note_tag nt
                                JOIN tag t ON nt.fk_tag_id = t.tag_id
                                WHERE nt.fk_note_id = n.note_id
                            ) AS tags,
                            (
                                SELECT GROUP_CONCAT(u.user_id || ':' || u.fname || ' ' || u.lname || ':' || sn2.permission, '|')
                                FROM shared_note sn2
                                JOIN user u ON sn2.fk_user_id = u.user_id
                                WHERE sn2.fk_note_id = n.note_id
                            ) AS shared,
                            u.fname || ' ' || u.lname AS owner,
                            sn.permission
                        FROM note n
                        JOIN subject s ON n.fk_subject_id = s.subject_id
                        JOIN user u ON n.fk_user_id = u.user_id
                        JOIN shared_note sn ON n.note_id = sn.fk_note_id
                        WHERE sn.fk_user_id = ?
                        ORDER BY n.updated_at DESC;'''

# Temp function for editor
def get_note_content(note_id):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], f'file_{note_id}.txt')
    if os.path.exists(filepath):
        with open(filepath, 'r') as file:
            content = file.read()
        return filepath, content
    return None, None


def allowed_file(filename) -> bool:
    """
    Check if a file is an allowed filetype
    :param filename: Full name of file
    :return: True if file is allowed, else False
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def create_connection(db_file: str) -> sqlite3.Connection|None:
    """
    Creates and returns a database connection
    :param db_file: Database path to connect to
    :return: Connection with database or None if error encountered
    """
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except sqlite3.Error as e:
        print(e)
        print('Error while connecting to database')
        return None


def insert(query: str, data: tuple) -> None:
    """
    Inserts a query into the database
    :param query: Query to insert
    :param data: Data to insert
    :param redirect_loc: Location to redirect to if error
    :return: Redirect if location given and error encountered
    """
    con = create_connection(DB_PATH)
    try:
        with con:
            con.execute(query, data)
    finally:
        con.close()


def fetch(query: str, arguments: tuple = (), fetch_all: bool = True) -> list:
    """
    Returns data from the database
    :param query: Query for database
    :param arguments: Arguments for query if applicable
    :param fetch_all: When true, fetch all rows, else only fetch first row
    :return: List of values returned by query
    """
    con = create_connection(DB_PATH)
    cur = con.cursor()
    cur.execute(query, arguments)
    if fetch_all:
        data = cur.fetchall()
    else:
        data = cur.fetchone()
    con.close()

    return data


def is_logged_in() -> bool:
    """
    Check if user has logged in or not
    :return: True if user has logged in else False
    """
    if session.get('email') is None:
        return False
    else:
        return True


def process_note(note) -> dict:
    """
    Takes data from database and converts it into a structured dictionary for display
    :param note: Tuple from database query
    :return: Dict with named fields
    """
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], f'file_{note[0]}.txt')
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        content = ''
    
    truncated_content = content[:150] + '...' if len(content) > 150 else content

    tags = []
    tag_ids = []
    shared = []

    if note[4]:
        for tag in note[4].split('|'):
            tag_id, tag_name = tag.split(':')
            tags.append({'id': int(tag_id), 'name': tag_name})
            tag_ids.append(int(tag_id))

    if note[5]:
        for user in note[5].split('|'):
            user_id, user_name, user_permission = user.split(':')
            shared.append({'id': int(user_id), 'name': user_name, 'permission': int(user_permission)})

    note_data = {
        'id': note[0],
        'title': note[1],
        'subject': note[2],
        'subject_id': int(note[3]),
        'tags': tags,
        'tag_ids': tag_ids,
        'shared': shared,
        'content': truncated_content
    }

    if len(note) > 6:
        note_data['owner'] = note[6]
        note_data['permission'] = note[7]
    
    return note_data


@app.route('/')
def index():
    """
    Renders the index page
    :return: Rendered index page
    """
    return render_template('index.html', title='home', logged_in=is_logged_in())


@app.route('/about')
def about():
    """
    Renders the about page
    :return: Rendered about page
    """
    return render_template('about.html', title='about', logged_in=is_logged_in())


@app.route('/dashboard')
def dashboard():
    """
    Renders the dashboard page
    :return: Rendered dashboard page
    """
    if not is_logged_in():
        return redirect(url_for('index'))
    
    note_list = fetch(NOTE_LIST_QUERY, (session['userid'], ))

    shared_list = fetch(SHARED_LIST_QUERY, (session['userid'], ))
    
    for i, note in enumerate(note_list):
        note_list[i] = process_note(note)

    for i, note in enumerate(shared_list):
        shared_list[i] = process_note(note)

    subject_list = fetch('SELECT subject_id, name FROM subject WHERE fk_user_id=?', (session['userid'],))
    tag_list = fetch('SELECT tag_id, name FROM tag WHERE fk_user_id IS NULL OR fk_user_id=?', (session['userid'],))

    subject_list = [{'id': subject[0], 'name': subject[1]} for subject in subject_list]
    tag_list = [{'id': tag[0], 'name': tag[1]} for tag in tag_list]

    return render_template('dashboard.html',
                           title='dashboard',
                           logged_in=is_logged_in(),
                           notes=note_list,
                           shared=shared_list,
                           subjects=subject_list,
                           tags=tag_list)


@app.route('/more/<int:shared>')
def more(shared):
    if shared:
        note_list = fetch(SHARED_LIST_QUERY, (session['userid'], ))
    else:
        note_list = fetch(NOTE_LIST_QUERY, (session['userid'], ))

    for i, note in enumerate(note_list):
        note_list[i] = process_note(note)
    
    subject_list = fetch('SELECT subject_id, name FROM subject WHERE fk_user_id=?', (session['userid'],))
    tag_list = fetch('SELECT tag_id, name FROM tag WHERE fk_user_id IS NULL OR fk_user_id=?', (session['userid'],))

    subject_list = [{'id': subject[0], 'name': subject[1]} for subject in subject_list]
    tag_list = [{'id': tag[0], 'name': tag[1]} for tag in tag_list]


    return render_template('more.html', 
                           shared=shared, 
                           notes=note_list, 
                           title=f'All {'Shared' if shared else 'Notes'}',
                           subjects=subject_list,
                           tags=tag_list,
                           logged_in=is_logged_in)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Renders the login page and logs in user
    :return: Rendered login page or redirect to index page
    """
    if is_logged_in():
        return redirect(url_for('index'))
    
    error = None
    form_data = {'email': ''}

    if request.method == 'POST':
        email = request.form.get('email').strip().lower()
        password = request.form.get('password')

        form_data.update({'email': email})

        user_data = fetch('SELECT user_id, fname, lname, password, role FROM user WHERE email = ?', (email,))

        try:
            userid = user_data[0][0]
            firstname = user_data[0][1]
            lastname = user_data[0][2]
            db_password = user_data[0][3]
            role = user_data[0][4]
        except IndexError:
            error = 'Email or password is invalid.'
            return render_template('login.html', title='login', logged_in=is_logged_in(), error=error, form_data=form_data)
        
        if not bcrypt.check_password_hash(db_password, password):
            error = 'Email or password is invalid.'
            return render_template('login.html', title='login', logged_in=is_logged_in(), error=error, form_data=form_data)
        
        session['email'] = email
        session['userid'] = userid
        session['firstname'] = firstname
        session['lastname'] = lastname
        session['role'] = role
        return redirect(url_for('index'))

    return render_template('login.html', title='login', logged_in=is_logged_in(), error=error, form_data=form_data)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    Render signup page and signup new users
    :return: Rendered signup page or redirect to login page
    """
    if is_logged_in():
        return redirect(url_for('index'))
    
    error = None
    form_data = {
        'fname': '',
        'lname': '',
        'email': '',
        'role': ''
    }

    if request.method == 'POST':
        fname = request.form.get('fname').strip().title()
        lname = request.form.get('lname').strip().title()
        email = request.form.get('email').strip().lower()
        password = request.form.get('password')
        password2 = request.form.get('password2')
        role = request.form.get('role')

        form_data.update({'fname': fname, 'lname': lname, 'email': email, 'role': role})

        if password != password2:
            error = "Passwords don't match."
            return render_template('signup.html', title='signup', logged_in=is_logged_in(),
                                   error=error, form_data=form_data)
        
        if role == '2':
            admin_password = request.form.get('admin-password', '')
            if admin_password != ADMIN_PASSWORD:
                error = "Invalid admin password."
                return render_template('signup.html', title='signup', logged_in=is_logged_in(),
                                       error=error, form_data=form_data)

        hashed_password = bcrypt.generate_password_hash(password)

        try:
            insert('INSERT INTO user(user_id, fname, lname, email, password, role) VALUES(NULL,?,?,?,?,?)',
                (fname, lname, email, hashed_password, role))
        except sqlite3.IntegrityError as e:
            error = "Email already exists or invalid data."
            return render_template('signup.html', title='signup', logged_in=is_logged_in(), error=error, form_data=form_data)


        return redirect(url_for('login'))

    return render_template('signup.html', title='signup', logged_in=is_logged_in(), error=error, form_data=form_data)


@app.route('/logout')
def logout():
    """
    Logs out user and redirects to login page
    :return: Redirect to the login page
    """
    [session.pop(key) for key in list(session.keys())]
    return redirect(url_for('login'))


@app.route('/account')
def account():
    """
    Renders the account page for user information
    :return: Rendered account page
    """
    if not is_logged_in():
        return redirect(url_for('index'))

    return render_template('account.html', title='account', logged_in=is_logged_in())


@app.route('/upload', methods=['POST'])
def upload():
    """
    Upload file to database
    :return: Redirect to dashboard page
    """
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

    cur.execute('INSERT INTO note (fk_user_id, fk_subject_id, title) VALUES (?, ?, ?)', (session['userid'], subject, title))
    note_id = cur.lastrowid

    if file and file.filename and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        new_filename = f"file_{note_id}.{ext}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
    else:
        new_filename = f"file_{note_id}.txt"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('')

    con.commit()
    con.close()
    
    return redirect(url_for('dashboard'))


@app.route('/edit/<int:note_id>', methods=['GET', 'POST'])
def edit_note(note_id):
    """
    Edit note text
    :param note_id: Note id for editing
    :return: Render of editor page
    """
    if not is_logged_in():
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        content = request.form['content']
        filepath = request.form['filepath']
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(content)
        insert('UPDATE note set updated_at = CURRENT_TIMESTAMP WHERE note_id = ?', (note_id, ))
        return redirect(url_for('dashboard'))

    filepath, content = get_note_content(note_id)
    if filepath:
        return render_template('editor.html', title='Editor', content=content, filepath=filepath, note_id=note_id)
    return "File not found", 404


@app.route('/toggle', methods=['POST'])
def toggle():
    data = request.get_json()
    note_id = data['note_id']
    tag_id = data['tag_id']
    action = data['action']

    if action:
        insert('INSERT OR IGNORE INTO note_tag (fk_note_id, fk_tag_id) VALUES (?, ?)', (note_id, tag_id))
    else:
        insert('DELETE FROM note_tag WHERE fk_note_id = ? AND fk_tag_id = ?', (note_id, tag_id))

    return jsonify({'success': True})


@app.route('/process-tags/<int:note_id>')
def process_tags(note_id):
    tag_list = fetch('''SELECT t.tag_id, t.name 
          FROM tag t JOIN note_tag nt ON t.tag_id=nt.fk_tag_id 
          WHERE nt.fk_note_id=? ORDER BY t.tag_id;''',
          (note_id, ))
    note_list = fetch('''SELECT n.note_id, s.name
                    FROM note n JOIN subject s ON fk_subject_id = subject_id
                    WHERE n.note_id=?''',
                    (note_id, ),
                    False)
    
    tag_list = [{'id': tag[0], 'name': tag[1]} for tag in tag_list]
    note_list = {'id': note_list[0], 'subject': note_list[1], 'tags': tag_list}

    return render_template('/partials/update/tag_list.html', tags=tag_list, note=note_list)


@app.route('/add-tag', methods=['POST'])
def add_tag():
    data = request.get_json()
    tag_name = data.get('tag_name', '').strip()

    if not tag_name:
        return jsonify({'success': False, 'error': 'Invalid input'})

    tag = fetch('SELECT * FROM tag WHERE name=? AND fk_user_id=?', (tag_name, session['userid']), False)
    if not tag:
        insert('INSERT INTO tag (name, fk_user_id) VALUES (?, ?)', (tag_name, session['userid']))
        tag = fetch('SELECT * FROM tag WHERE name=? AND fk_user_id=?', (tag_name, session['userid']), False)

    return jsonify({'success': True, 'tag_id': tag[0], 'tag_name': tag[2]})


@app.route('/delete/<int:note_id>', methods=['POST'])
def delete(note_id):
    if not is_logged_in():
        return redirect(url_for('login'))
    
    owner = fetch("SELECT fk_user_id FROM note WHERE note_id = ?", (note_id,), False)
    if not owner or owner[0] != session['userid']:
        return "Unauthorized", 403


    insert('DELETE FROM note_tag WHERE fk_note_id = ?', (note_id, ))
    insert('DELETE FROM note WHERE note_id = ?', (note_id, ))
    filename = f'file_{note_id}.txt'
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        

    return redirect(url_for('dashboard'))


@app.route('/copy/<int:note_id>', methods=['POST'])
def copy(note_id):
    if not is_logged_in():
        return redirect(url_for('login'))
    
    title = request.form.get('title')
    copy_tags = request.form.get('tags')
    copy_shared = request.form.get('shared')

    tags = []
    shared = []
    source = os.path.join(app.config['UPLOAD_FOLDER'], f'file_{note_id}.txt')

    con = create_connection(DB_PATH)
    cur = con.cursor()
    cur.execute('SELECT * FROM note WHERE note_id=?', (note_id, ))
    note = cur.fetchone()

    cur.execute('INSERT INTO note (fk_user_id, fk_subject_id, title) VALUES (?, ?, ?)', (session['userid'], note[2], title or f'Copy of {note[3]}'))
    note_id = cur.lastrowid

    if copy_tags:
        cur.execute('SELECT * FROM note_tag WHERE fk_note_id=?', (note[0], ))
        tags = cur.fetchall()

    if copy_shared:
        cur.execute('SELECT * FROM shared_note WHERE fk_note_id=? AND fk_user_id!=?', (note[0], session['userid']))
        shared = cur.fetchall()
        if note[1] != session['userid']:
            shared.append((note[0], note[1], 2))

    destination = os.path.join(app.config['UPLOAD_FOLDER'], f'file_{note_id}.txt')
    shutil.copyfile(source, destination)

    for tag in tags:
        cur.execute('INSERT INTO note_tag (fk_note_id, fk_tag_id) VALUES (?, ?)', (note_id, tag[1]))
    
    for user in shared:
        cur.execute('INSERT INTO shared_note (fk_note_id, fk_user_id, permission) VALUES (?, ?, ?)', (note_id, user[1], user[2]))

    con.commit()
    con.close()

    return redirect(url_for('dashboard'))


# Sharing
@app.route('/modify-share', methods=['POST'])
def modify_share():
    if not is_logged_in():
        return jsonify({'error': 'Not logged in'}), 400
    data = request.get_json()
    user_id = data['user_id']
    note_id = data['note_id']
    action = data['action']
    permission = data.get('permission')

    if action == 'share':
        # Prevent sharing with same person twice
        exists = fetch(
            'SELECT 1 FROM shared_note WHERE fk_user_id=? AND fk_note_id=?',
            (user_id, note_id),
            False
        )
        if exists:
            return jsonify({'error': 'This user is already shared with'}), 400

        # Prevents sharing with invalid user
        user = fetch('SELECT user_id FROM user WHERE user_id=?', (user_id,), False)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Prevents sharing with yourself
        if str(user_id) == str(session['userid']):
            return jsonify({'error': 'You cannot share with yourself'}), 400


        insert('INSERT INTO shared_note (fk_user_id, fk_note_id, permission) VALUES (?, ?, ?)',
               (user_id, note_id, permission))
        return '', 204
    
    elif action == 'update':
        insert('UPDATE shared_note SET permission=? WHERE fk_user_id=? AND fk_note_id=?',
               (permission, user_id, note_id))
        return '', 204

    elif action == 'unshare':
        insert('DELETE FROM shared_note WHERE fk_user_id=? AND fk_note_id=?',
               (user_id, note_id))
        return '', 204

    return jsonify({'error': 'Invalid action'}), 400


@app.route('/process-shared/<int:note_id>')
def process_shared(note_id):
    shared_list = fetch('''SELECT u.user_id, GROUP_CONCAT(u.fname || ' ' || u.lname, '|'), sn.permission
          FROM shared_note sn LEFT JOIN user u ON u.user_id=sn.fk_user_id 
          WHERE sn.fk_note_id=? GROUP BY u.user_id;''',
          (note_id, ))
    
    shared_list = [{'id': user[0], 'name': user[1], 'permission': user[2]} for user in shared_list]
    note_list = {'id': note_id, 'shared': shared_list}

    return render_template('/partials/update/share_list.html', note=note_list)


@app.route('/search-users')
def search_users():
    if not is_logged_in():
        return jsonify({'error': 'Not logged in'}), 400

    query = request.args.get('q', '').strip()

    if not query:
        return jsonify([])

    users = fetch(
        '''SELECT user_id, fname, lname, email FROM user 
           WHERE user_id LIKE ? OR fname LIKE ? OR lname LIKE ? OR email LIKE ?
           LIMIT 10''',
        (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%')
    )

    return jsonify([
        {
            'id': user[0],
            'label': f"{user[1]} {user[2]} ({user[3]})",
            'email': user[3]
        }
        for user in users
    ])

@app.route('/note_options/<int:note_id>', methods=['POST'])
def note_options(note_id):
    title = request.form.get('change-name', '').strip()
    subject = request.form.get('subject')
    new_subject = request.form.get('new-subject').strip()

    con = create_connection(DB_PATH)
    cur = con.cursor()

    cur.execute('SELECT title FROM note WHERE note_id=?', (note_id, ))
    note_data = cur.fetchone()
    print(note_data)

    print(title)

    if not title:
        title = note_data[0]
    
    print(title)

    if subject == 'add-new' and new_subject:
        cur.execute('INSERT INTO subject (fk_user_id, name) VALUES (?, ?)', (session['userid'], new_subject))
        subject = cur.lastrowid

    cur.execute('UPDATE note SET fk_subject_id=?, title=? WHERE note_id=?', (subject, title, note_id))

    con.commit()
    con.close()
    
    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.run(debug=True)

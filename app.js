import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here' # Replace with a strong secret key for production

DATABASE = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # This allows accessing columns by name
    return conn

def create_table():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reg_number TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            class TEXT NOT NULL,
            term TEXT NOT NULL,
            fee_status TEXT NOT NULL CHECK(fee_status IN ('Paid', 'Defaulter'))
        )
    ''')
    conn.commit()
    conn.close()

# Call create_table when the app starts
with app.app_context():
    create_table()

@app.route('/')
def index():
    conn = get_db_connection()
    students = conn.execute('SELECT * FROM students ORDER BY class, name').fetchall()
    conn.close()
    return render_template('index.html', students=students)

@app.route('/register', methods=('GET', 'POST'))
def register_student():
    if request.method == 'POST':
        reg_number = request.form['reg_number'].strip()
        name = request.form['name'].strip()
        student_class = request.form['class'].strip()
        term = request.form['term'].strip()
        fee_status = request.form['fee_status']

        if not all([reg_number, name, student_class, term, fee_status]):
            flash('All fields are required!', 'error')
        else:
            conn = get_db_connection()
            try:
                conn.execute(
                    'INSERT INTO students (reg_number, name, class, term, fee_status) VALUES (?, ?, ?, ?, ?)',
                    (reg_number, name, student_class, term, fee_status)
                )
                conn.commit()
                flash(f'Student {name} registered successfully!', 'success')
                return redirect(url_for('index'))
            except sqlite3.IntegrityError:
                flash(f'Registration number "{reg_number}" already exists.', 'error')
            finally:
                conn.close()
    return render_template('register_student.html')

@app.route('/student/<string:reg_number>')
def student_details(reg_number):
    conn = get_db_connection()
    student = conn.execute('SELECT * FROM students WHERE reg_number = ?', (reg_number,)).fetchone()
    conn.close()
    if student is None:
        flash('Student not found!', 'error')
        return redirect(url_for('index'))
    return render_template('student_details.html', student=student)

@app.route('/students')
def student_list():
    conn = get_db_connection()
    # Get filters from query parameters
    status_filter = request.args.get('status', 'all')
    class_filter = request.args.get('class', 'all')
    term_filter = request.args.get('term', 'all')

    query = 'SELECT * FROM students WHERE 1=1'
    params = []

    if status_filter != 'all':
        query += ' AND fee_status = ?'
        params.append(status_filter)
    if class_filter != 'all':
        query += ' AND class = ?'
        params.append(class_filter)
    if term_filter != 'all':
        query += ' AND term = ?'
        params.append(term_filter)

    query += ' ORDER BY class, name'
    students = conn.execute(query, params).fetchall()

    # Get distinct classes and terms for filter dropdowns
    classes = [row['class'] for row in conn.execute('SELECT DISTINCT class FROM students ORDER BY class').fetchall()]
    terms = [row['term'] for row in conn.execute('SELECT DISTINCT term FROM students ORDER BY term').fetchall()]

    conn.close()
    return render_template(
        'student_list.html',
        students=students,
        status_filter=status_filter,
        class_filter=class_filter,
        term_filter=term_filter,
        classes=classes,
        terms=terms
    )

@app.route('/student/<int:student_id>/update_status', methods=('POST',))
def update_fee_status(student_id):
    new_status = request.form['new_status']
    conn = get_db_connection()
    try:
        conn.execute('UPDATE students SET fee_status = ? WHERE id = ?', (new_status, student_id))
        conn.commit()
        flash('Fee status updated successfully!', 'success')
    except Exception as e:
        flash(f'Error updating status: {e}', 'error')
    finally:
        conn.close()
    # Redirect back to the page they came from, or a default list
    return redirect(request.referrer or url_for('student_list'))


if __name__ == '__main__':
    app.run(debug=True) # debug=True allows automatic reloading and provides a debugger
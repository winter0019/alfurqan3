import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from . import get_db, bcrypt # Import the bcrypt object

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))
    return render_template('login.html')

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

        # Check password with bcrypt
        if user and bcrypt.check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['role'] = user['role']
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@main_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.login'))

@main_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    if session.get('role') == 'admin':
        return render_template('admin_dashboard.html')
    else:
        return render_template('dashboard.html')

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role', 'user') # Default role is user

        db = get_db()
        try:
            # Hash password with bcrypt before storing
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            db.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, hashed_password, role),
            )
            db.commit()
            flash('Registration successful! Please log in.')
            return redirect(url_for('main.login'))
        except sqlite3.IntegrityError:
            flash('Username already exists.')
    return render_template('register.html')

@main_bp.route('/students', methods=['GET', 'POST'])
def students():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    db = get_db()
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        date_of_birth = request.form.get('date_of_birth')
        gender = request.form.get('gender')
        enrollment_date = request.form.get('enrollment_date')

        db.execute(
            "INSERT INTO students (first_name, last_name, date_of_birth, gender, enrollment_date) VALUES (?, ?, ?, ?, ?)",
            (first_name, last_name, date_of_birth, gender, enrollment_date),
        )
        db.commit()
        flash('Student added successfully!')
        return redirect(url_for('main.students'))

    students_list = db.execute('SELECT * FROM students').fetchall()
    return render_template('students.html', students=students_list)

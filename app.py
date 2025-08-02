from flask import Flask, render_template, request, redirect, url_for, session, flash, g
import sqlite3
import hashlib
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_super_secret_key_here' # !! CHANGE THIS IN PRODUCTION !!

# Database configuration
DATABASE = 'database.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row # This allows fetching rows as dictionary-like objects
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user'
            );
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reg_no TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                date_of_birth DATE,
                class TEXT NOT NULL,
                term TEXT NOT NULL,
                academic_year TEXT NOT NULL,
                fee_status TEXT NOT NULL DEFAULT 'Defaulter',
                guardian_name TEXT,
                guardian_phone TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                term TEXT NOT NULL,
                academic_year TEXT NOT NULL,
                expected_amount REAL NOT NULL,
                paid_amount REAL NOT NULL DEFAULT 0.0,
                last_payment_date TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id)
            );
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                term TEXT NOT NULL,
                academic_year TEXT NOT NULL,
                amount_paid REAL NOT NULL,
                payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                recorded_by TEXT,
                FOREIGN KEY (student_id) REFERENCES students(id)
            );
        ''')
        db.commit()

        # Create a default admin user if one doesn't exist
        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        if cursor.fetchone() is None:
            hashed_password = hashlib.sha256('adminpassword'.encode()).hexdigest()
            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                           ('admin', hashed_password, 'admin'))
            db.commit()
            print("Default admin user 'admin' with password 'adminpassword' created.")


# Context processor to inject 'now' into all templates
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# Password hashing utility
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Jinja2 custom filter for currency formatting
@app.template_filter('format_currency')
def format_currency_filter(value):
    """
    Formats a number as currency with commas and two decimal places.
    Handles None or non-numeric values gracefully.
    """
    try:
        # Ensure value is treated as a float, default to 0.0 if None
        numeric_value = float(value) if value is not None else 0.0
        return "{:,.2f}".format(numeric_value)
    except (ValueError, TypeError):
        # Return the original value if it's not a valid number,
        # or an empty string/0.0 if you prefer for display.
        # For currency, returning 0.00 for non-numeric might be better.
        return "0.00" 

# --- Routes ---

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = hash_password(password)

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, hashed_password))
        user = cursor.fetchone()

        if user:
            session['username'] = user['username']
            session['role'] = user['role']
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/create_user', methods=['GET', 'POST'])
def create_user():
    if 'username' not in session or session['role'] != 'admin':
        flash('Unauthorized access.', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form.get('role', 'user') # Default to 'user' if not specified

        db = get_db()
        cursor = db.cursor()

        try:
            hashed_password = hash_password(password)
            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                           (username, hashed_password, role))
            db.commit()
            flash(f"User '{username}' created successfully as {role}!", 'success')
            return redirect(url_for('create_user'))
        except sqlite3.IntegrityError:
            flash(f"Username '{username}' already exists. Please choose a different username.", 'error')
        except Exception as e:
            flash(f"An error occurred: {e}", 'error')

    return render_template('create_user.html')


@app.route('/register_student', methods=['GET', 'POST'])
def register_student():
    if 'username' not in session:
        flash('Please log in to register a student.', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        reg_no = request.form['reg_no'].strip()
        name = request.form['name'].strip()
        date_of_birth = request.form['date_of_birth']
        class_name = request.form['class']
        term = request.form['term']
        academic_year = request.form['academic_year']
        guardian_name = request.form.get('guardian_name', '').strip()
        guardian_phone = request.form.get('guardian_phone', '').strip()
        
        # Validate expected_fee
        try:
            expected_fee = float(request.form['expected_fee'])
            if expected_fee < 0:
                flash('Expected fee cannot be negative.', 'error')
                return render_template('register_student.html') # Render the form again
        except ValueError:
            flash('Invalid expected fee. Please enter a valid number.', 'error')
            return render_template('register_student.html') # Render the form again


        db = get_db()
        cursor = db.cursor()

        try:
            # Insert student
            cursor.execute("INSERT INTO students (reg_no, name, date_of_birth, class, term, academic_year, guardian_name, guardian_phone) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                           (reg_no, name, date_of_birth, class_name, term, academic_year, guardian_name, guardian_phone))
            student_id = cursor.lastrowid

            # Insert initial fee record
            cursor.execute("INSERT INTO fees (student_id, term, academic_year, expected_amount) VALUES (?, ?, ?, ?)",
                           (student_id, term, academic_year, expected_fee))
            db.commit()
            flash(f'Student {name} (Reg No: {reg_no}) registered successfully with fee of ₦{expected_fee:,.2f}!', 'success')
            return redirect(url_for('register_student'))
        except sqlite3.IntegrityError:
            flash(f"Registration number '{reg_no}' already exists. Please use a unique registration number.", 'error')
        except Exception as e:
            flash(f"An error occurred: {e}", 'error')

    return render_template('register_student.html')


@app.route('/student_list')
def student_list():
    if 'username' not in session:
        flash('Please log in to view student list.', 'error')
        return redirect(url_for('login'))

    db = get_db()
    cursor = db.cursor()

    # Filtering logic
    search_query = request.args.get('search', '').strip()
    selected_class = request.args.get('class', '')
    selected_term = request.args.get('term', '')
    selected_fee_status = request.args.get('fee_status', '')

    query = """
        SELECT
            s.id,
            s.reg_no,
            s.name,
            s.class,
            s.term,
            s.academic_year,
            SUM(f.expected_amount) AS total_expected_fee,
            SUM(f.paid_amount) AS total_paid_fee
        FROM students s
        LEFT JOIN fees f ON s.id = f.student_id
        WHERE 1=1
    """
    params = []

    if search_query:
        query += " AND (s.name LIKE ? OR s.reg_no LIKE ? OR s.guardian_name LIKE ?)"
        params.extend([f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'])
    if selected_class:
        query += " AND s.class = ?"
        params.append(selected_class)
    if selected_term:
        query += " AND s.term = ?"
        params.append(selected_term)

    query += " GROUP BY s.id ORDER BY s.name ASC"

    students = cursor.execute(query, params).fetchall()

    # Post-process for fee status filtering and actual fee status
    filtered_students = []
    for student in students:
        expected_fee_val = student['total_expected_fee'] if student['total_expected_fee'] is not None else 0
        paid_fee_val = student['total_paid_fee'] if student['total_paid_fee'] is not None else 0
        
        outstanding = expected_fee_val - paid_fee_val
        fee_status = 'N/A' # Default for no fee records for this student
        
        if expected_fee_val > 0: # Only assign status if there's an expected fee
            if outstanding <= 0:
                fee_status = 'Paid'
            elif paid_fee_val > 0:
                fee_status = 'Partially Paid'
            else: # outstanding > 0 and paid == 0
                fee_status = 'Defaulter'
        
        if not selected_fee_status or fee_status == selected_fee_status:
            student_dict = dict(student)
            student_dict['fee_status_display'] = fee_status
            student_dict['outstanding_fee'] = max(0, outstanding) # Ensure no negative outstanding
            filtered_students.append(student_dict)

    # Fetch unique classes, terms for filter dropdowns
    classes = [row[0] for row in cursor.execute("SELECT DISTINCT class FROM students ORDER BY class").fetchall()]
    terms = [row[0] for row in cursor.execute("SELECT DISTINCT term FROM students ORDER BY term").fetchall()]
    fee_statuses = ['Paid', 'Partially Paid', 'Defaulter', 'N/A']

    return render_template('student_list.html',
                           students=filtered_students,
                           classes=classes,
                           terms=terms,
                           fee_statuses=fee_statuses,
                           selected_class=selected_class,
                           selected_term=selected_term,
                           selected_fee_status=selected_fee_status,
                           search_query=search_query)


@app.route('/student/<int:student_id>')
def student_details(student_id):
    if 'username' not in session:
        flash('Please log in to view student details.', 'error')
        return redirect(url_for('login'))

    db = get_db()
    cursor = db.cursor()

    student = cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    if not student:
        flash('Student not found.', 'error')
        return redirect(url_for('student_list'))

    # Fetch fee breakdown for each term
    fee_breakdown = cursor.execute("SELECT term, academic_year, expected_amount, paid_amount FROM fees WHERE student_id = ? ORDER BY academic_year DESC, term DESC", (student_id,)).fetchall()

    # Calculate current fee status
    total_expected = sum(row['expected_amount'] for row in fee_breakdown if row['expected_amount'] is not None)
    total_paid = sum(row['paid_amount'] for row in fee_breakdown if row['paid_amount'] is not None)
    current_outstanding = max(0, total_expected - total_paid)

    current_fee_status = 'N/A'
    if total_expected > 0:
        if current_outstanding <= 0:
            current_fee_status = 'Paid'
        elif current_outstanding > 0 and total_paid > 0:
            current_fee_status = 'Partially Paid'
        else: # outstanding > 0 and total_paid == 0
            current_fee_status = 'Defaulter'

    # Fetch payment history
    payment_history = cursor.execute("SELECT * FROM payments WHERE student_id = ? ORDER BY payment_date DESC", (student_id,)).fetchall()

    return render_template('student_details.html',
                           student=student,
                           fee_breakdown=fee_breakdown,
                           payment_history=payment_history,
                           current_fee_status=current_fee_status,
                           current_outstanding=current_outstanding)


@app.route('/edit_student/<int:student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    if 'username' not in session:
        flash('Please log in to edit student details.', 'error')
        return redirect(url_for('login'))

    db = get_db()
    cursor = db.cursor()

    student = cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    if not student:
        flash('Student not found.', 'error')
        return redirect(url_for('student_list'))

    if request.method == 'POST':
        reg_no = request.form['reg_no'].strip()
        name = request.form['name'].strip()
        date_of_birth = request.form['date_of_birth']
        class_name = request.form['class']
        term = request.form['term']
        academic_year = request.form['academic_year']
        guardian_name = request.form.get('guardian_name', '').strip()
        guardian_phone = request.form.get('guardian_phone', '').strip()

        try:
            cursor.execute("UPDATE students SET reg_no = ?, name = ?, date_of_birth = ?, class = ?, term = ?, academic_year = ?, guardian_name = ?, guardian_phone = ?, last_updated = CURRENT_TIMESTAMP WHERE id = ?",
                           (reg_no, name, date_of_birth, class_name, term, academic_year, guardian_name, guardian_phone, student_id))
            db.commit()
            flash(f'Student {name} (Reg No: {reg_no}) updated successfully!', 'success')
            return redirect(url_for('student_details', student_id=student_id))
        except sqlite3.IntegrityError:
            flash(f"Registration number '{reg_no}' already exists for another student. Please use a unique registration number.", 'error')
        except Exception as e:
            flash(f"An error occurred: {e}", 'error')

    return render_template('edit_student.html', student=student)


@app.route('/delete_student/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    if 'username' not in session or session['role'] != 'admin':
        flash('Unauthorized access.', 'error')
        return redirect(url_for('login'))

    db = get_db()
    cursor = db.cursor()
    try:
        # Delete related fees and payments first (cascading delete if foreign keys were set up with ON DELETE CASCADE, but safer to do explicitly if not)
        cursor.execute("DELETE FROM fees WHERE student_id = ?", (student_id,))
        cursor.execute("DELETE FROM payments WHERE student_id = ?", (student_id,))
        cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
        db.commit()
        flash('Student and all associated records deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting student: {e}', 'error')
    return redirect(url_for('student_list'))


@app.route('/record_payment/<int:student_id>', methods=['GET', 'POST'])
def record_payment(student_id):
    if 'username' not in session:
        flash('Please log in to record payments.', 'error')
        return redirect(url_for('login'))

    db = get_db()
    cursor = db.cursor()

    student = cursor.execute("SELECT id, name FROM students WHERE id = ?", (student_id,)).fetchone()
    if not student:
        flash('Student not found.', 'error')
        return redirect(url_for('student_list'))

    # Get available terms/academic years from fees table
    available_fees = cursor.execute("SELECT term, academic_year, expected_amount, paid_amount FROM fees WHERE student_id = ? ORDER BY academic_year DESC, term DESC", (student_id,)).fetchall()
    
    # Pre-calculate outstanding for each term
    terms_with_outstanding = []
    for fee in available_fees:
        expected = fee['expected_amount'] if fee['expected_amount'] is not None else 0
        paid = fee['paid_amount'] if fee['paid_amount'] is not None else 0
        term_outstanding = expected - paid
        if term_outstanding > 0: # Only show terms with outstanding balance
            terms_with_outstanding.append(dict(fee, outstanding=max(0, term_outstanding)))


    if request.method == 'POST':
        term = request.form['term']
        academic_year = request.form['academic_year']
        amount_paid_str = request.form['amount_paid']
        recorded_by = session['username']

        try:
            amount_paid = float(amount_paid_str)
            if amount_paid <= 0:
                flash('Payment amount must be positive.', 'error')
                return redirect(url_for('record_payment', student_id=student_id))

            # Find the fee record for the specific term and academic year
            fee_record = cursor.execute("SELECT * FROM fees WHERE student_id = ? AND term = ? AND academic_year = ?",
                                         (student_id, term, academic_year)).fetchone()

            if fee_record:
                new_paid_amount = fee_record['paid_amount'] + amount_paid
                
                # Check if overpaying (optional, but good practice)
                if new_paid_amount > fee_record['expected_amount']:
                    flash(f'Warning: Payment exceeds outstanding balance for {term} {academic_year}. Please adjust.', 'warning')
                    # You might want to prevent the payment or allow it and calculate change
                    # For now, we'll allow it to go slightly over, but the message warns the user.

                # Update fees table
                cursor.execute("UPDATE fees SET paid_amount = ?, last_payment_date = CURRENT_TIMESTAMP WHERE id = ?",
                               (new_paid_amount, fee_record['id']))

                # Insert into payments history
                cursor.execute("INSERT INTO payments (student_id, term, academic_year, amount_paid, recorded_by) VALUES (?, ?, ?, ?, ?)",
                               (student_id, term, academic_year, amount_paid, recorded_by))
                
                db.commit()
                flash(f'Payment of ₦{amount_paid:,.2f} recorded successfully for {student["name"]} ({term} {academic_year})!', 'success')
                return redirect(url_for('student_details', student_id=student_id))
            else:
                flash('Fee record for the specified term/academic year not found. Please ensure the student has fees registered for this period.', 'error')
        except ValueError:
            flash('Invalid amount entered. Please enter a number.', 'error')
        except Exception as e:
            flash(f"An error occurred: {e}", 'error')

    return render_template('record_payment.html', student=student, terms_with_outstanding=terms_with_outstanding)


@app.route('/admin_dashboard')
def admin_dashboard():
    if 'username' not in session or session['role'] != 'admin':
        flash('Unauthorized access.', 'error')
        return redirect(url_for('login'))

    db = get_db()
    cursor = db.cursor()

    # Total students
    total_students = cursor.execute("SELECT COUNT(*) FROM students").fetchone()[0]

    # Fee Status Summary
    # Join students and fees to get aggregated data
    cursor.execute("""
        SELECT
            s.id,
            s.name,
            s.reg_no,
            s.class,
            s.term,
            s.academic_year,
            SUM(f.expected_amount) AS total_expected_for_student,
            SUM(f.paid_amount) AS total_paid_for_student
        FROM students s
        LEFT JOIN fees f ON s.id = f.student_id
        GROUP BY s.id, s.name, s.reg_no, s.class, s.term, s.academic_year
    """)
    student_fee_data = cursor.fetchall()

    paid_students_count = 0
    defaulters_count = 0
    partially_paid_count = 0
    total_expected_revenue = 0.0
    total_received_revenue = 0.0
    outstanding_defaulter_students = [] # For specific defaulters list
    outstanding_partially_paid_students = [] # For specific partially paid list


    for student_data in student_fee_data:
        expected = student_data['total_expected_for_student'] if student_data['total_expected_for_student'] is not None else 0.0
        paid = student_data['total_paid_for_student'] if student_data['total_paid_for_student'] is not None else 0.0
        outstanding = expected - paid

        total_expected_revenue += expected
        total_received_revenue += paid

        if expected > 0: # Only consider students with registered fees for status
            if outstanding <= 0:
                paid_students_count += 1
            elif paid > 0:
                partially_paid_count += 1
                outstanding_partially_paid_students.append({
                    'reg_no': student_data['reg_no'],
                    'name': student_data['name'],
                    'class': student_data['class'],
                    'term': student_data['term'],
                    'academic_year': student_data['academic_year'],
                    'outstanding_amount': max(0, outstanding) # Ensure non-negative
                })
            else: # outstanding > 0 and paid == 0
                defaulters_count += 1
                outstanding_defaulter_students.append({
                    'reg_no': student_data['reg_no'],
                    'name': student_data['name'],
                    'class': student_data['class'],
                    'term': student_data['term'],
                    'academic_year': student_data['academic_year'],
                    'outstanding_amount': max(0, outstanding) # Ensure non-negative
                })

    total_outstanding_revenue = max(0, total_expected_revenue - total_received_revenue)

    # Get recent activities (e.g., recent payments)
    recent_payments = cursor.execute("""
        SELECT p.payment_date, s.name, p.amount_paid, p.recorded_by, p.term, p.academic_year
        FROM payments p
        JOIN students s ON p.student_id = s.id
        ORDER BY p.payment_date DESC
        LIMIT 10
    """).fetchall()

    return render_template('admin_dashboard.html',
                           total_students=total_students,
                           paid_students_count=paid_students_count,
                           defaulters_count=defaulters_count,
                           partially_paid_count=partially_paid_count,
                           total_expected_revenue=total_expected_revenue,
                           total_received_revenue=total_received_revenue,
                           total_outstanding_revenue=total_outstanding_revenue,
                           outstanding_defaulter_students=outstanding_defaulter_students,
                           outstanding_partially_paid_students=outstanding_partially_paid_students,
                           recent_payments=recent_payments)


if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=8000)

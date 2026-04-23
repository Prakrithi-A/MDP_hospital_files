from flask import Flask, render_template, request, redirect, url_for, session
import os
import sqlite3

app = Flask(__name__)
app.secret_key = "supersecretkey"

UPLOAD_FOLDER = 'uploads'
DB_FILE = 'hospital.db'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ---------------- DATABASE INIT ----------------

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # USERS (login only)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT,
            password TEXT,
            role TEXT
        )
    ''')

    # PATIENT INFO
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            patient_id TEXT PRIMARY KEY,
            full_name TEXT,
            gender TEXT,
            age INTEGER,
            phone TEXT,
            emergency_contact TEXT
        )
    ''')

    # DOCTOR INFO
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doctors (
            doctor_id TEXT PRIMARY KEY,
            full_name TEXT,
            specialization TEXT,
            experience TEXT,
            position TEXT,
            working_hours TEXT,
            phone TEXT,
            license_number TEXT,
            qualification TEXT
        )
    ''')

    conn.commit()
    conn.close()

# ---------------- LOGIN ----------------

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def handle_login():
    role = request.form.get('role')
    user_id = request.form.get('user_id')

    session['role'] = role
    session['user_id'] = user_id

    if role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif role == 'doctor':
        return redirect(url_for('doctor_dashboard', doctor_id=user_id))
    elif role == 'patient':
        return redirect(url_for('patient_dashboard', patient_id=user_id))
    elif role == 'external':
        return redirect(url_for('external_dashboard'))

    return redirect(url_for('login'))

# ---------------- DASHBOARDS ----------------

@app.route('/admin')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    return render_template('admin_dashboard.html')

@app.route('/doctor/<doctor_id>')
def doctor_dashboard(doctor_id):
    if session.get('role') != 'doctor':
        return redirect(url_for('login'))
    return render_template('doctor_dashboard.html')

@app.route('/patient/<patient_id>')
def patient_dashboard(patient_id):
    if session.get('role') != 'patient':
        return redirect(url_for('login'))
    return render_template('patient_dashboard.html')

@app.route('/external')
def external_dashboard():
    return render_template('external.html')

# ---------------- ADD PATIENT ----------------

@app.route('/add_patient', methods=['GET', 'POST'])
def add_patient():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    message = ""

    if request.method == 'POST':
        data = (
            request.form['patient_id'],
            request.form['full_name'],
            request.form['gender'],
            request.form['age'],
            request.form['phone'],
            request.form['emergency_contact']
        )

        try:
            cursor.execute("INSERT INTO patients VALUES (?, ?, ?, ?, ?, ?)", data)
            conn.commit()
            message = "Patient added successfully"
        except:
            message = "Patient already exists"

    conn.close()
    return render_template('add_patient.html', message=message)

# ---------------- ADD DOCTOR ----------------

@app.route('/add_doctor', methods=['GET', 'POST'])
def add_doctor():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    message = ""

    if request.method == 'POST':
        data = (
            request.form['doctor_id'],
            request.form['full_name'],
            request.form['specialization'],
            request.form['experience'],
            request.form['position'],
            request.form['working_hours'],
            request.form['phone'],
            request.form['license_number'],
            request.form['qualification']
        )

        try:
            cursor.execute("INSERT INTO doctors VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", data)
            conn.commit()
            message = "Doctor added successfully"
        except:
            message = "Doctor already exists"

    conn.close()
    return render_template('add_doctor.html', message=message)

# ---------------- VIEW PATIENT INFO ----------------

@app.route('/patient_info', methods=['GET', 'POST'])
def patient_info():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    patient = None

    if request.method == 'POST':
        patient_id = request.form['patient_id']
        cursor.execute("SELECT * FROM patients WHERE patient_id=?", (patient_id,))
        patient = cursor.fetchone()

    conn.close()
    return render_template('patient_info.html', patient=patient)

# ---------------- VIEW DOCTOR INFO ----------------

@app.route('/doctor_info', methods=['GET', 'POST'])
def doctor_info():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    doctor = None

    if request.method == 'POST':
        doctor_id = request.form['doctor_id']
        cursor.execute("SELECT * FROM doctors WHERE doctor_id=?", (doctor_id,))
        doctor = cursor.fetchone()

    conn.close()
    return render_template('doctor_info.html', doctor=doctor)

# ---------------- RUN ----------------

if __name__ == '__main__':
    init_db()   # 🔥 THIS CREATES TABLES
    app.run(debug=True)
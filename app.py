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

    # USERS TABLE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT,
            phone TEXT,
            password TEXT,
            role TEXT
        )
    ''')

    # MAPPING TABLE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mapping (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id TEXT,
            patient_id TEXT
        )
    ''')

    # PATIENT INFO TABLE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patient_info (
            patient_id TEXT PRIMARY KEY,
            name TEXT,
            gender TEXT,
            age INTEGER,
            blood_group TEXT,
            phone TEXT,
            emergency_contact TEXT,
            relation TEXT
        )
    ''')

    # DOCTOR INFO TABLE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doctor_info (
            doctor_id TEXT PRIMARY KEY,
            name TEXT,
            specialization TEXT,
            experience TEXT,
            phone TEXT
        )
    ''')

    conn.commit()
    conn.close()

# ---------------- LOGIN ----------------

@app.route('/')
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

# ---------------- LOGOUT ----------------

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ---------------- ADMIN DASHBOARD ----------------

@app.route('/admin')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    return render_template('admin_dashboard.html')

# ---------------- ADD USER ----------------

@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    message = ""

    if request.method == 'POST':
        user_id = request.form.get('user_id')
        username = request.form.get('username')
        phone = request.form.get('phone')
        password = request.form.get('password')
        role = request.form.get('role')

        try:
            cursor.execute(
                "INSERT INTO users VALUES (?, ?, ?, ?, ?)",
                (user_id, username, phone, password, role)
            )
            conn.commit()
            message = "User added successfully"
        except:
            message = "User already exists"

    conn.close()
    return render_template('add_user.html', message=message)

# ---------------- ADD PATIENT INFO ----------------

@app.route('/add_patient', methods=['GET', 'POST'])
def add_patient():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    message = ""

    if request.method == 'POST':
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO patient_info VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                request.form['patient_id'],
                request.form['name'],
                request.form['gender'],
                request.form['age'],
                request.form['blood_group'],
                request.form['phone'],
                request.form['emergency_contact'],
                request.form['relation']
            ))
            conn.commit()
            message = "Patient info added"
        except:
            message = "Already exists"

        conn.close()

    return render_template('add_patient.html', message=message)

# ---------------- ADD DOCTOR INFO ----------------

@app.route('/add_doctor', methods=['GET', 'POST'])
def add_doctor():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    message = ""

    if request.method == 'POST':
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO doctor_info VALUES (?, ?, ?, ?, ?)
            ''', (
                request.form['doctor_id'],
                request.form['name'],
                request.form['specialization'],
                request.form['experience'],
                request.form['phone']
            ))
            conn.commit()
            message = "Doctor info added"
        except:
            message = "Already exists"

        conn.close()

    return render_template('add_doctor.html', message=message)

# ---------------- VIEW PATIENT INFO ----------------

@app.route('/patient_info', methods=['GET', 'POST'])
def patient_info():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    data = None

    if request.method == 'POST':
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM patient_info WHERE patient_id=?", 
                       (request.form['patient_id'],))
        data = cursor.fetchone()

        conn.close()

    return render_template('patient_info.html', data=data)

# ---------------- VIEW DOCTOR INFO ----------------

@app.route('/doctor_info', methods=['GET', 'POST'])
def doctor_info():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    data = None

    if request.method == 'POST':
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM doctor_info WHERE doctor_id=?", 
                       (request.form['doctor_id'],))
        data = cursor.fetchone()

        conn.close()

    return render_template('doctor_info.html', data=data)

# ---------------- MAPPING ----------------

@app.route('/mapping', methods=['GET', 'POST'])
def mapping():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    message = ""

    if request.method == 'POST':
        cursor.execute(
            "INSERT INTO mapping (doctor_id, patient_id) VALUES (?, ?)",
            (request.form['doctor_id'], request.form['patient_id'])
        )
        conn.commit()
        message = "Mapping added"

    cursor.execute("SELECT * FROM mapping")
    mappings = cursor.fetchall()

    conn.close()
    return render_template('mapping.html', mappings=mappings, message=message)

# ---------------- VIEW RECORDS ----------------

@app.route('/patients')
def patients():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    files = os.listdir(UPLOAD_FOLDER)
    return render_template('all_records.html', files=files)

# ---------------- UPLOAD ----------------

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        file = request.files.get('file')
        patient_id = request.form.get('patient_id')
        doctor_id = request.form.get('doctor_id')

        if file and patient_id and doctor_id:
            filename = f"{patient_id}_{doctor_id}_{file.filename}"
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            return "Uploaded successfully"

    return render_template('upload.html')

# ---------------- DOCTOR DASHBOARD ----------------

@app.route('/doctor/<doctor_id>', methods=['GET', 'POST'])
def doctor_dashboard(doctor_id):
    if session.get('role') != 'doctor':
        return redirect(url_for('login'))

    files = os.listdir(UPLOAD_FOLDER)
    doctor_files = [f for f in files if f.split('_')[1] == doctor_id] if files else []

    return render_template('doctor_dashboard.html', files=doctor_files, doctor_id=doctor_id)

# ---------------- PATIENT DASHBOARD ----------------

@app.route('/patient/<patient_id>')
def patient_dashboard(patient_id):
    if session.get('role') != 'patient':
        return redirect(url_for('login'))

    files = os.listdir(UPLOAD_FOLDER)
    patient_files = [f for f in files if f.startswith(patient_id + "_")]

    return render_template('patient_dashboard.html', files=patient_files, patient_id=patient_id)

# ---------------- EXTERNAL ----------------

@app.route('/external')
def external_dashboard():
    if session.get('role') != 'external':
        return redirect(url_for('login'))
    return render_template('external.html')

# ---------------- RUN ----------------

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
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

    # USERS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT,
            phone TEXT,
            password TEXT,
            role TEXT
        )
    ''')

    # MAPPING
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mapping (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id TEXT,
            patient_id TEXT
        )
    ''')

    # PATIENT INFO
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patient_info (
            patient_id TEXT PRIMARY KEY,
            name TEXT,
            gender TEXT,
            age INTEGER,
            phone TEXT,
            emergency_contact TEXT,
            history TEXT
        )
    ''')

    # DOCTOR INFO
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doctor_info (
            doctor_id TEXT PRIMARY KEY,
            name TEXT,
            specialization TEXT,
            experience INTEGER,
            phone TEXT,
            license TEXT
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

        if not all([user_id, username, phone, password, role]):
            message = "All fields required"
        else:
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

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    message = ""

    if request.method == 'POST':
        try:
            cursor.execute('''
                INSERT INTO patient_info VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                request.form.get('patient_id'),
                request.form.get('name'),
                request.form.get('gender'),
                request.form.get('age'),
                request.form.get('phone'),
                request.form.get('emergency'),
                request.form.get('history')
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

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    message = ""

    if request.method == 'POST':
        try:
            cursor.execute('''
                INSERT INTO doctor_info VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                request.form.get('doctor_id'),
                request.form.get('name'),
                request.form.get('specialization'),
                request.form.get('experience'),
                request.form.get('phone'),
                request.form.get('license')
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
                       (request.form.get('patient_id'),))
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
                       (request.form.get('doctor_id'),))
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
        doctor_id = request.form.get('doctor_id')
        patient_id = request.form.get('patient_id')

        cursor.execute("INSERT INTO mapping (doctor_id, patient_id) VALUES (?, ?)",
                       (doctor_id, patient_id))
        conn.commit()
        message = "Mapping added"

    cursor.execute("SELECT doctor_id, patient_id FROM mapping")
    mappings = cursor.fetchall()

    conn.close()
    return render_template('mapping.html', mappings=mappings, message=message)

# ---------------- VIEW FILES ----------------

@app.route('/patients')
def patients():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    files = os.listdir(UPLOAD_FOLDER)
    return render_template('all_records.html', files=files)

# ---------------- DELETE FILE ----------------

@app.route('/delete_file/<filename>')
def delete_file(filename):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(path):
        os.remove(path)

    return redirect(url_for('patients'))

# ---------------- UPLOAD ----------------

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        file = request.files.get('file')
        patient_id = request.form.get('patient_id')
        doctor_id = request.form.get('doctor_id')

        if file:
            filename = f"{patient_id}_{doctor_id}_{file.filename}"
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            return "Uploaded successfully"

    return render_template('upload.html')

# ---------------- DASHBOARDS ----------------

@app.route('/doctor/<doctor_id>')
def doctor_dashboard(doctor_id):
    if session.get('role') != 'doctor':
        return redirect(url_for('login'))

    files = os.listdir(UPLOAD_FOLDER)
    doctor_files = [f for f in files if len(f.split('_')) > 1 and f.split('_')[1] == doctor_id]

    return render_template('doctor_dashboard.html', files=doctor_files)

@app.route('/patient/<patient_id>')
def patient_dashboard(patient_id):
    if session.get('role') != 'patient':
        return redirect(url_for('login'))

    files = os.listdir(UPLOAD_FOLDER)
    patient_files = [f for f in files if f.startswith(patient_id + "_")]

    return render_template('patient_dashboard.html', files=patient_files)

@app.route('/external')
def external_dashboard():
    return render_template('external.html')

# ---------------- RUN ----------------

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
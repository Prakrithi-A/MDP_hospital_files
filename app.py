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

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT,
            phone TEXT,
            password TEXT,
            role TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mapping (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id TEXT,
            patient_id TEXT
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

    if not user_id:
        user_id = "guest"

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

# ---------------- ADMIN ----------------

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

        cursor.execute("SELECT * FROM users WHERE id=? AND role='doctor'", (doctor_id,))
        doctor = cursor.fetchone()

        cursor.execute("SELECT * FROM users WHERE id=? AND role='patient'", (patient_id,))
        patient = cursor.fetchone()

        if doctor and patient:
            cursor.execute(
                "INSERT INTO mapping (doctor_id, patient_id) VALUES (?, ?)",
                (doctor_id, patient_id)
            )
            conn.commit()
            message = "Mapping added successfully"
        else:
            message = "Doctor or Patient does not exist"

    cursor.execute("SELECT doctor_id, patient_id FROM mapping")
    mappings = cursor.fetchall()

    conn.close()

    return render_template('mapping.html', mappings=mappings, message=message)

# ---------------- DOCTOR ----------------

@app.route('/doctor/<doctor_id>', methods=['GET', 'POST'])
def doctor_dashboard(doctor_id):
    if session.get('role') != 'doctor':
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT patient_id FROM mapping WHERE doctor_id=?", (doctor_id,))
    linked_patients = [row[0] for row in cursor.fetchall()]

    files = []
    message = ""

    if request.method == 'POST':
        patient_id = request.form.get('patient_id')

        if patient_id not in linked_patients:
            message = "Access Denied"
        else:
            files = [f for f in os.listdir(UPLOAD_FOLDER) if f.startswith(patient_id + "_")]

    conn.close()

    return render_template(
        'doctor_dashboard.html',
        files=files,
        doctor_id=doctor_id,
        message=message,
        linked_patients=linked_patients
    )

# ---------------- PATIENT ----------------

@app.route('/patient/<patient_id>')
def patient_dashboard(patient_id):
    if session.get('role') != 'patient':
        return redirect(url_for('login'))

    files = [f for f in os.listdir(UPLOAD_FOLDER) if f.startswith(patient_id + "_")]

    return render_template('patient_dashboard.html', files=files, patient_id=patient_id)

# ---------------- EXTERNAL ----------------

@app.route('/external')
def external_dashboard():
    if session.get('role') != 'external':
        return redirect(url_for('login'))
    return render_template('external.html')

# ---------------- VIEW ALL RECORDS ----------------

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
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            return "File uploaded successfully"

        return "Missing data"

    return render_template('upload.html')

# ---------------- RUN ----------------

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
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

# ---------------- DATABASE ----------------

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
        CREATE TABLE IF NOT EXISTS patient_info (
            patient_id TEXT PRIMARY KEY,
            name TEXT,
            gender TEXT,
            dob TEXT,
            blood_group TEXT,
            phone TEXT,
            emergency_contact TEXT,
            relation TEXT
        )
    ''')

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

    session['role'] = role.lower() if role else ""
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
    return render_template('admin_dashboard.html')

# ---------------- ADD USER ----------------

@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    message = ""

    if request.method == 'POST':
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()

            role = request.form['role'].lower()   # normalize role

            cursor.execute(
                "INSERT INTO users VALUES (?, ?, ?, ?, ?)",
                (
                    request.form['user_id'],
                    request.form['username'],
                    request.form['phone'],
                    request.form['password'],
                    role
                )
            )

            conn.commit()
            message = "User added successfully"
        except Exception as e:
            message = f"Error: {e}"
        finally:
            conn.close()

    return render_template('add_user.html', message=message)

# ---------------- ADD / UPDATE PATIENT ----------------

@app.route('/add_patient', methods=['GET', 'POST'])
def add_patient():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # DEBUG PRINT
    cursor.execute("SELECT * FROM users")
    print("USERS TABLE:", cursor.fetchall())

    # case-insensitive fetch
    cursor.execute("SELECT id FROM users WHERE LOWER(role)='patient'")
    patient_ids = [row[0] for row in cursor.fetchall()]

    message = ""
    data = None

    if request.method == 'POST':
        patient_id = request.form['patient_id']
        action = request.form['action']

        cursor.execute(
            "SELECT * FROM users WHERE LOWER(id)=LOWER(?) AND LOWER(role)='patient'",
            (patient_id,)
        )
        user = cursor.fetchone()

        print("USER CHECK:", user)

        if not user:
            message = "Patient login not found"
        else:
            cursor.execute("SELECT * FROM patient_info WHERE patient_id=?", (patient_id,))
            existing = cursor.fetchone()

            if action == "add":
                if existing:
                    message = "Already exists, use update"
                else:
                    cursor.execute('''
                        INSERT INTO patient_info VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        patient_id,
                        request.form['name'],
                        request.form['gender'],
                        request.form['dob'],
                        request.form['blood_group'],
                        request.form['phone'],
                        request.form['emergency_contact'],
                        request.form['relation']
                    ))
                    conn.commit()
                    message = "Patient info added"

            elif action == "update":
                if not existing:
                    message = "No data to update"
                else:
                    cursor.execute('''
                        UPDATE patient_info SET
                        name=?, gender=?, dob=?, blood_group=?, phone=?, emergency_contact=?, relation=?
                        WHERE patient_id=?
                    ''', (
                        request.form['name'],
                        request.form['gender'],
                        request.form['dob'],
                        request.form['blood_group'],
                        request.form['phone'],
                        request.form['emergency_contact'],
                        request.form['relation'],
                        patient_id
                    ))
                    conn.commit()
                    message = "Patient info updated"

            data = existing

    conn.close()
    return render_template('add_patient.html', patient_ids=patient_ids, message=message, data=data)

# ---------------- ADD / UPDATE DOCTOR ----------------

@app.route('/add_doctor', methods=['GET', 'POST'])
def add_doctor():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE LOWER(role)='doctor'")
    doctor_ids = [row[0] for row in cursor.fetchall()]

    message = ""
    data = None

    if request.method == 'POST':
        doctor_id = request.form['doctor_id']
        action = request.form['action']

        cursor.execute(
            "SELECT * FROM users WHERE LOWER(id)=LOWER(?) AND LOWER(role)='doctor'",
            (doctor_id,)
        )
        user = cursor.fetchone()

        if not user:
            message = "Doctor login not found"
        else:
            cursor.execute("SELECT * FROM doctor_info WHERE doctor_id=?", (doctor_id,))
            existing = cursor.fetchone()

            if action == "add":
                if existing:
                    message = "Already exists, use update"
                else:
                    cursor.execute('''
                        INSERT INTO doctor_info VALUES (?, ?, ?, ?, ?)
                    ''', (
                        doctor_id,
                        request.form['name'],
                        request.form['specialization'],
                        request.form['experience'],
                        request.form['phone']
                    ))
                    conn.commit()
                    message = "Doctor info added"

            elif action == "update":
                if not existing:
                    message = "No data to update"
                else:
                    cursor.execute('''
                        UPDATE doctor_info SET
                        name=?, specialization=?, experience=?, phone=?
                        WHERE doctor_id=?
                    ''', (
                        request.form['name'],
                        request.form['specialization'],
                        request.form['experience'],
                        request.form['phone'],
                        doctor_id
                    ))
                    conn.commit()
                    message = "Doctor info updated"

            data = existing

    conn.close()
    return render_template('add_doctor.html', doctor_ids=doctor_ids, message=message, data=data)

# ---------------- DASHBOARDS ----------------

@app.route('/doctor/<doctor_id>')
def doctor_dashboard(doctor_id):
    return render_template('doctor_dashboard.html', doctor_id=doctor_id)

@app.route('/patient/<patient_id>')
def patient_dashboard(patient_id):
    return render_template('patient_dashboard.html', patient_id=patient_id)

@app.route('/external')
def external_dashboard():
    return render_template('external.html')

# ---------------- OTHER ROUTES ----------------

@app.route('/upload')
def upload():
    return render_template('upload.html')

@app.route('/patients')
def patients():
    return render_template('all_records.html')

@app.route('/mapping')
def mapping():
    return render_template('mapping.html')

@app.route('/doctors')
def doctors():
    return render_template('doctors.html')

@app.route('/patient_info')
def patient_info():
    return render_template('patient_info.html')

@app.route('/doctor_info')
def doctor_info():
    return render_template('doctor_info.html')

# ---------------- RUN ----------------

if __name__ == '__main__':
    print("Using DB:", DB_FILE)
    init_db()
    app.run(debug=True)
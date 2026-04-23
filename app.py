from flask import Flask, render_template, request, redirect, url_for, session
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

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

    if not role:
        return redirect(url_for('login'))

    # store session
    session['role'] = role
    session['user_id'] = user_id

    # redirect based on role
    if role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif role == 'doctor':
        return redirect(url_for('doctor_dashboard', doctor_id=user_id))
    elif role == 'patient':
        return redirect(url_for('patient_dashboard', patient_id=user_id))
    elif role == 'external':
        return redirect(url_for('external_dashboard'))

    return redirect(url_for('login'))

# ---------------- ADMIN ----------------

@app.route('/admin')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    return render_template('admin_dashboard.html')

# ---------------- DOCTOR ----------------

@app.route('/doctor/<doctor_id>')
def doctor_dashboard(doctor_id):
    if session.get('role') != 'doctor':
        return redirect(url_for('login'))

    files = os.listdir(UPLOAD_FOLDER)
    doctor_files = []

    for f in files:
        parts = f.split('_')
        if len(parts) >= 2 and parts[1] == doctor_id:
            doctor_files.append(f)

    return render_template(
        'doctor_dashboard.html',
        files=doctor_files,
        doctor_id=doctor_id
    )

# ---------------- PATIENT ----------------

@app.route('/patient/<patient_id>')
def patient_dashboard(patient_id):
    if session.get('role') != 'patient':
        return redirect(url_for('login'))

    files = os.listdir(UPLOAD_FOLDER)
    patient_files = [f for f in files if f.startswith(patient_id + "_")]

    return render_template(
        'patient_dashboard.html',
        files=patient_files,
        patient_id=patient_id
    )

# ---------------- EXTERNAL ----------------

@app.route('/external')
def external_dashboard():
    if session.get('role') != 'external':
        return redirect(url_for('login'))
    return render_template('external.html')

# ---------------- ADMIN FEATURES ----------------

@app.route('/patients')
def patients():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    files = os.listdir(UPLOAD_FOLDER)
    return render_template('all_records.html', files=files)

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
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            return "Uploaded successfully"

        return "Missing data"

    return render_template('upload.html')

@app.route('/add_user')
def add_user():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    return render_template('add_user.html')

@app.route('/mapping')
def mapping():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    return render_template('mapping.html')

@app.route('/doctors')
def doctors():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    return render_template('doctors.html')

# ---------------- LOGOUT ----------------

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ---------------- RUN ----------------

if __name__ == '__main__':
    app.run(debug=True)
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os

app = Flask(__name__)

# ---------------- CONFIG ----------------

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ---------------- LOGIN ----------------

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def handle_login():
    role = request.form.get('role')
    user_id = request.form.get('user_id')

    print("LOGIN:", role, user_id)

    if role == 'external':
        return redirect(url_for('external'))

    if not user_id:
        user_id = "guest"

    if role == 'admin':
        return redirect(url_for('admin'))

    elif role == 'doctor':
        return redirect(url_for('doctor', doctor_id=user_id))

    elif role == 'patient':
        return redirect(url_for('patient', patient_id=user_id))

    return "Invalid role ❌"

# ---------------- DASHBOARDS ----------------

@app.route('/admin')
def admin():
    return render_template('admin_dashboard.html')

@app.route('/doctor/<doctor_id>')
def doctor(doctor_id):
    files = os.listdir('uploads')

    doctor_files = []
    for f in files:
        parts = f.split('_')
        if len(parts) >= 2 and parts[1] == doctor_id:
            doctor_files.append(f)

    return render_template('doctor_dashboard.html', files=doctor_files, doctor_id=doctor_id)

@app.route('/patient/<patient_id>')
def patient(patient_id):
    files = os.listdir('uploads')

    patient_files = []
    for f in files:
        if f.startswith(patient_id + "_"):
            patient_files.append(f)

    return render_template('patient_dashboard.html', files=patient_files, patient_id=patient_id)

@app.route('/external')
def external():
    return render_template('external.html')

# ---------------- VIEW ALL RECORDS (NEW) ----------------

@app.route('/patients')
def patients():
    files = os.listdir('uploads')
    return render_template('all_records.html', files=files)

# ---------------- UPLOAD ----------------

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files.get('file')
        patient_id = request.form.get('patient_id')
        doctor_id = request.form.get('doctor_id')

        if file and patient_id and doctor_id:
            filename = f"{patient_id}_{doctor_id}_{file.filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            return "File uploaded successfully! ✅"

        return "Missing data ❌"

    return render_template('upload.html')

# ---------------- DOWNLOAD ----------------

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory('uploads', filename)

# ---------------- OTHER ----------------

@app.route('/doctors')
def doctors():
    return "Doctor List Page"

@app.route('/mapping')
def mapping():
    return "Doctor-Patient Mapping Page"

# ---------------- RUN ----------------

if __name__ == '__main__':
    app.run(debug=True)
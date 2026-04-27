from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = "supersecretkey"

DB_FILE = "hospital.db"
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- DATABASE ----------------

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT,
        phone TEXT,
        password TEXT,
        role TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS patient_info (
        patient_id TEXT PRIMARY KEY,
        name TEXT,
        gender TEXT,
        dob TEXT,
        blood_group TEXT,
        phone TEXT,
        emergency_contact TEXT,
        relation TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS doctor_info (
        doctor_id TEXT PRIMARY KEY,
        name TEXT,
        specialization TEXT,
        experience TEXT,
        phone TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS doctor_patient_map (
        doctor_id TEXT,
        patient_id TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doctor_id TEXT,
        patient_id TEXT,
        file_name TEXT,
        file_path TEXT,
        notes TEXT,
        review_date TEXT
    )""")

    conn.commit()
    conn.close()

# ---------------- AUTH ----------------

def login_required(role=None):
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "role" not in session:
                return redirect(url_for("login"))
            if role and session["role"] != role:
                return "Access Denied ❌", 403
            return f(*args, **kwargs)
        return decorated
    return wrapper

# ---------------- LOGIN ----------------

@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    uid = request.form["user_id"]
    pwd = request.form["password"]
    role = request.form["role"].lower()

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id=? AND password=? AND role=?",
                (uid, pwd, role))
    user = cur.fetchone()
    conn.close()

    if not user:
        return "Invalid credentials ❌"

    session["role"] = role
    session["user_id"] = uid

    return redirect(url_for(f"{role}_dashboard"))

# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------------- DASHBOARDS ----------------

@app.route("/admin")
@login_required("admin")
def admin_dashboard():
    return render_template("admin_dashboard.html")

@app.route("/doctor")
@login_required("doctor")
def doctor_dashboard():
    return render_template("doctor_dashboard.html")

@app.route("/patient")
@login_required("patient")
def patient_dashboard():
    return render_template("patient_dashboard.html")

# ---------------- ADD USER ----------------

@app.route("/add_user", methods=["GET", "POST"])
@login_required("admin")
def add_user():
    msg = ""
    if request.method == "POST":
        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)",
                    (request.form["user_id"],
                     request.form["username"],
                     request.form["phone"],
                     request.form["password"],
                     request.form["role"]))
        conn.commit()
        conn.close()
        msg = "User added"
    return render_template("add_user.html", message=msg)

# ---------------- ADD PATIENT ----------------

@app.route("/add_patient", methods=["GET", "POST"])
@login_required("admin")
def add_patient():
    msg = ""
    if request.method == "POST":
        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO patient_info VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (request.form["patient_id"],
                     request.form["name"],
                     request.form["gender"],
                     request.form["dob"],
                     request.form["blood_group"],
                     request.form["phone"],
                     request.form["emergency_contact"],
                     request.form["relation"]))
        conn.commit()
        conn.close()
        msg = "Patient added"
    return render_template("add_patient.html", message=msg)

# ---------------- ADD DOCTOR ----------------

@app.route("/add_doctor", methods=["GET", "POST"])
@login_required("admin")
def add_doctor():
    msg = ""
    if request.method == "POST":
        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO doctor_info VALUES (?, ?, ?, ?, ?)",
                    (request.form["doctor_id"],
                     request.form["name"],
                     request.form["specialization"],
                     request.form["experience"],
                     request.form["phone"]))
        conn.commit()
        conn.close()
        msg = "Doctor added"
    return render_template("add_doctor.html", message=msg)

# ---------------- VIEW PATIENTS ----------------

@app.route("/patient_info")
@login_required("admin")
def patient_info():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM patient_info")
    data = cur.fetchall()
    conn.close()
    return render_template("patient_info.html", patients=data)

# ---------------- VIEW DOCTORS ----------------

@app.route("/doctor_info")
@login_required("admin")
def doctor_info():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM doctor_info")
    data = cur.fetchall()
    conn.close()
    return render_template("doctor_info.html", doctors=data)

# ---------------- MAPPING (FIXED) ----------------

@app.route("/mapping", methods=["GET", "POST"])
@login_required("admin")
def mapping():
    msg = ""
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM doctor_info")
    doctors = cur.fetchall()

    cur.execute("SELECT * FROM patient_info")
    patients = cur.fetchall()

    if request.method == "POST":
        d = request.form["doctor_id"]
        p = request.form["patient_id"]

        cur.execute("INSERT INTO doctor_patient_map VALUES (?, ?)", (d, p))
        conn.commit()
        msg = "Mapped"

    cur.execute("SELECT * FROM doctor_patient_map")
    mappings = cur.fetchall()
    conn.close()

    return render_template("mapping.html",
                           doctors=doctors,
                           patients=patients,
                           mappings=mappings,
                           message=msg)

# ---------------- DOCTOR UPLOAD ----------------

@app.route("/doctor/upload_record", methods=["GET", "POST"])
@login_required("doctor")
def upload_record():
    msg = ""
    if request.method == "POST":
        file = request.files["file"]
        path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(path)

        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO records VALUES (NULL, ?, ?, ?, ?, ?, ?)",
                    (session["user_id"],
                     request.form["patient_id"],
                     file.filename,
                     path,
                     request.form.get("notes", ""),
                     request.form.get("review_date", "")))
        conn.commit()
        conn.close()
        msg = "Uploaded"

    return render_template("upload_record.html", message=msg)

# ---------------- DOCTOR VIEW PATIENT ----------------

@app.route("/doctor/view_patient_info", methods=["GET", "POST"])
@login_required("doctor")
def view_patient_info():
    patient = None

    if request.method == "POST":
        pid = request.form["patient_id"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM patient_info WHERE patient_id=?", (pid,))
        patient = cur.fetchone()
        conn.close()

    return render_template("doctor_view_patient_info.html",
                           patient=patient)

# ---------------- INIT ----------------

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
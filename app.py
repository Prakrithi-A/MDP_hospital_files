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

# ---------------- DASHBOARD ----------------

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

# ---------------- VIEW PATIENT (FIXED) ----------------

@app.route("/patient_info", methods=["GET", "POST"])
@login_required("admin")
def patient_info():
    data = None
    msg = ""

    if request.method == "POST":
        pid = request.form["patient_id"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM patient_info WHERE patient_id=?", (pid,))
        data = cur.fetchone()
        conn.close()

        if not data:
            msg = "No patient found ❌"

    return render_template("patient_info.html", data=data, message=msg)

# ---------------- VIEW DOCTOR (FIXED) ----------------

@app.route("/doctor_info", methods=["GET", "POST"])
@login_required("admin")
def doctor_info():
    data = None
    msg = ""

    if request.method == "POST":
        did = request.form["doctor_id"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM doctor_info WHERE doctor_id=?", (did,))
        data = cur.fetchone()
        conn.close()

        if not data:
            msg = "No doctor found ❌"

    return render_template("doctor_info.html", data=data, message=msg)

# ---------------- INIT ----------------

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
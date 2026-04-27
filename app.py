from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from functools import wraps

app = Flask(__name__)
app.secret_key = "supersecretkey"

DB_FILE = "hospital.db"

# ---------------- DATABASE ----------------

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT,
        phone TEXT,
        password TEXT,
        role TEXT
    )
    """)

    cursor.execute("""
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
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS doctor_info (
        doctor_id TEXT PRIMARY KEY,
        name TEXT,
        specialization TEXT,
        experience TEXT,
        phone TEXT
    )
    """)

    # ensure admin exists
    cursor.execute("SELECT * FROM users WHERE id='admin1'")
    if not cursor.fetchone():
        cursor.execute("""
        INSERT INTO users VALUES (?, ?, ?, ?, ?)
        """, ("admin1", "Admin", "9999999999", "123", "admin"))

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
                return "Access Denied", 403
            return f(*args, **kwargs)
        return decorated
    return wrapper

# ---------------- LOGIN ----------------

@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    role = request.form["role"].lower()
    user_id = request.form["user_id"]
    password = request.form["password"]

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM users WHERE id=? AND password=? AND role=?
    """, (user_id, password, role))

    user = cursor.fetchone()
    conn.close()

    if not user:
        return "Invalid credentials", 401

    session["role"] = role
    session["user_id"] = user_id

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

@app.route("/external")
def external_dashboard():
    return render_template("external.html")

# ---------------- ADD USER ----------------

@app.route("/add_user", methods=["GET", "POST"])
@login_required("admin")
def add_user():
    message = ""

    if request.method == "POST":
        conn = get_db()
        cursor = conn.cursor()

        try:
            cursor.execute("""
            INSERT INTO users VALUES (?, ?, ?, ?, ?)
            """, (
                request.form["user_id"],
                request.form["username"],
                request.form["phone"],
                request.form["password"],
                request.form["role"]
            ))
            conn.commit()
            message = "User added ✅"
        except sqlite3.IntegrityError:
            message = "User already exists ❌"

        conn.close()

    return render_template("add_user.html", message=message)

# ---------------- ADD PATIENT ----------------

@app.route("/add_patient", methods=["GET", "POST"])
@login_required("admin")
def add_patient():
    message = ""

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE role='patient'")
    patient_ids = [row["id"] for row in cursor.fetchall()]

    if request.method == "POST":
        try:
            cursor.execute("""
            INSERT INTO patient_info VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                request.form["patient_id"],
                request.form["name"],
                request.form["gender"],
                request.form["dob"],
                request.form["blood_group"],
                request.form["phone"],
                request.form["emergency_contact"],
                request.form["relation"]
            ))
            conn.commit()
            message = "Patient added ✅"
        except sqlite3.IntegrityError:
            message = "Already exists ❌"

    conn.close()
    return render_template("add_patient.html", patient_ids=patient_ids, message=message)

# ---------------- PATIENT INFO (FIXED) ----------------

@app.route("/patient_info", methods=["GET", "POST"])
@login_required("admin")
def patient_info():
    data = None
    message = ""

    if request.method == "POST":
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM patient_info WHERE patient_id=?",
                       (request.form["patient_id"],))
        data = cursor.fetchone()

        if not data:
            message = "Patient not found ❌"

        conn.close()

    return render_template("patient_info.html", data=data, message=message)

@app.route("/update_patient/<patient_id>", methods=["POST"])
@login_required("admin")
def update_patient(patient_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE patient_info
    SET name=?, gender=?, dob=?, blood_group=?, phone=?, emergency_contact=?, relation=?
    WHERE patient_id=?
    """, (
        request.form["name"],
        request.form["gender"],
        request.form["dob"],
        request.form["blood_group"],
        request.form["phone"],
        request.form["emergency_contact"],
        request.form["relation"],
        patient_id
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("patient_info"))

# ---------------- ADD DOCTOR ----------------

@app.route("/add_doctor", methods=["GET", "POST"])
@login_required("admin")
def add_doctor():
    message = ""

    if request.method == "POST":
        conn = get_db()
        cursor = conn.cursor()

        try:
            cursor.execute("""
            INSERT INTO doctor_info VALUES (?, ?, ?, ?, ?)
            """, (
                request.form["doctor_id"],
                request.form["name"],
                request.form["specialization"],
                request.form["experience"],
                request.form["phone"]
            ))
            conn.commit()
            message = "Doctor added ✅"
        except sqlite3.IntegrityError:
            message = "Doctor exists ❌"

        conn.close()

    return render_template("add_doctor.html", message=message)

# ---------------- DOCTOR INFO ----------------

@app.route("/doctor_info", methods=["GET", "POST"])
@login_required("admin")
def doctor_info():
    data = None
    message = ""

    if request.method == "POST":
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM doctor_info WHERE doctor_id=?",
                       (request.form["doctor_id"],))
        data = cursor.fetchone()

        if not data:
            message = "Doctor not found ❌"

        conn.close()

    return render_template("doctor_info.html", data=data, message=message)

@app.route("/update_doctor/<doctor_id>", methods=["POST"])
@login_required("admin")
def update_doctor(doctor_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE doctor_info
    SET name=?, specialization=?, experience=?, phone=?
    WHERE doctor_id=?
    """, (
        request.form["name"],
        request.form["specialization"],
        request.form["experience"],
        request.form["phone"],
        doctor_id
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("doctor_info"))

# ---------------- LIST PAGES ----------------

@app.route("/doctors")
@login_required("admin")
def doctors():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM doctor_info")
    doctors = cursor.fetchall()
    conn.close()
    return render_template("doctors.html", doctors=doctors)

@app.route("/patients")
@login_required("admin")
def patients():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patient_info")
    patients = cursor.fetchall()
    conn.close()
    return render_template("all_records.html", patients=patients)

# ---------------- EXTRA ----------------

@app.route("/upload")
@login_required("admin")
def upload():
    return render_template("upload.html")

@app.route("/mapping")
@login_required("admin")
def mapping():
    return render_template("mapping.html")

# ---------------- RUN ----------------

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
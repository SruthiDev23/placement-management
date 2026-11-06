from datetime import date
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = "change-this-to-a-long-random-secret-key"

# IMPORTANT: Replace YOUR_MYSQL_PASSWORD with your MySQL root password.
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "****",
    "database": "placement_management"
}

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

def login_required(role=None):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login"))
            if role and session.get("role") != role:
                flash("You are not allowed to access that page.", "error")
                return redirect(url_for("dashboard"))
            return view(*args, **kwargs)
        return wrapped
    return decorator

def create_default_admin():
    """Creates admin/admin123 only if no admin account exists."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users WHERE username=%s", ("admin",))
    if cur.fetchone() is None:
        cur.execute(
            "INSERT INTO users (username, password_hash, role, student_id) VALUES (%s,%s,'admin',NULL)",
            ("admin", generate_password_hash("admin123"))
        )
        conn.commit()
    cur.close()
    conn.close()

@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["user_id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            session["student_id"] = user["student_id"]
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.", "error")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        roll_no = request.form.get("roll_no", "").strip()
        branch = request.form.get("branch", "").strip()
        email = request.form.get("email", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        try:
            cgpa = float(request.form.get("cgpa", "0"))
            if not 0 <= cgpa <= 10:
                raise ValueError()
            if not all([name, roll_no, branch, email, username, password]):
                raise ValueError()
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO students (name, roll_no, branch, cgpa, email) VALUES (%s,%s,%s,%s,%s)",
                (name, roll_no, branch, cgpa, email)
            )
            student_id = cur.lastrowid
            cur.execute(
                "INSERT INTO users (username, password_hash, role, student_id) VALUES (%s,%s,'student',%s)",
                (username, generate_password_hash(password), student_id)
            )
            conn.commit()
            cur.close()
            conn.close()
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))
        except (ValueError, TypeError):
            flash("Enter valid details. CGPA must be between 0 and 10.", "error")
        except Error as e:
            flash(f"Could not register. Check duplicate roll number, email or username. Details: {e}", "error")
    return render_template("register.html")

@app.route("/dashboard")
@login_required()
def dashboard():
    if session["role"] == "student":
        return redirect(url_for("student_portal"))
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM students")
    students_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM companies")
    companies_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM applications")
    applications_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM applications WHERE status='Selected'")
    selected_count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return render_template("dashboard.html", students_count=students_count,
                           companies_count=companies_count,
                           applications_count=applications_count,
                           selected_count=selected_count)

@app.route("/students", methods=["GET", "POST"])
@login_required("admin")
def students():
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    if request.method == "POST":
        try:
            cur.execute(
                "INSERT INTO students (name, roll_no, branch, cgpa, email) VALUES (%s,%s,%s,%s,%s)",
                (request.form["name"].strip(), request.form["roll_no"].strip(),
                 request.form["branch"].strip(), float(request.form["cgpa"]),
                 request.form["email"].strip())
            )
            conn.commit()
            flash("Student added successfully.", "success")
        except (Error, ValueError) as e:
            conn.rollback()
            flash(f"Could not add student: {e}", "error")
    cur.execute("SELECT * FROM students ORDER BY student_id DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("students.html", students=rows)

@app.route("/companies", methods=["GET", "POST"])
@login_required("admin")
def companies():
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    if request.method == "POST":
        try:
            cur.execute(
                "INSERT INTO companies (company_name, job_role, package, eligibility_cgpa, drive_date) VALUES (%s,%s,%s,%s,%s)",
                (request.form["company_name"].strip(), request.form["job_role"].strip(),
                 float(request.form["package"]), float(request.form["eligibility_cgpa"]),
                 request.form["drive_date"])
            )
            conn.commit()
            flash("Company/job added successfully.", "success")
        except (Error, ValueError) as e:
            conn.rollback()
            flash(f"Could not add company: {e}", "error")
    cur.execute("SELECT * FROM companies ORDER BY company_id DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("companies.html", companies=rows)

@app.route("/applications")
@login_required()
def applications():
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    if session["role"] == "admin":
        cur.execute("""
            SELECT a.application_id, s.name, s.roll_no, c.company_name,
                   c.job_role, a.applied_date, a.round, a.status
            FROM applications a
            JOIN students s ON a.student_id=s.student_id
            JOIN companies c ON a.company_id=c.company_id
            ORDER BY a.application_id DESC
        """)
    else:
        cur.execute("""
            SELECT a.application_id, s.name, s.roll_no, c.company_name,
                   c.job_role, a.applied_date, a.round, a.status
            FROM applications a
            JOIN students s ON a.student_id=s.student_id
            JOIN companies c ON a.company_id=c.company_id
            WHERE a.student_id=%s ORDER BY a.application_id DESC
        """, (session["student_id"],))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("applications.html", applications=rows)

@app.route("/applications/<int:application_id>/status", methods=["POST"])
@login_required("admin")
def update_status(application_id):
    status = request.form.get("status")
    allowed = ["Applied", "Shortlisted", "Selected", "Rejected"]
    if status not in allowed:
        flash("Invalid application status.", "error")
    else:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE applications SET status=%s WHERE application_id=%s",
                    (status, application_id))
        conn.commit()
        cur.close()
        conn.close()
        flash("Application status updated.", "success")
    return redirect(url_for("applications"))

@app.route("/student")
@login_required("student")
def student_portal():
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM students WHERE student_id=%s", (session["student_id"],))
    student = cur.fetchone()
    cur.execute("""
        SELECT c.*, a.application_id, a.status
        FROM companies c
        LEFT JOIN applications a
        ON c.company_id=a.company_id AND a.student_id=%s
        ORDER BY c.drive_date
    """, (session["student_id"],))
    companies = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("student_portal.html", student=student, companies=companies)

@app.route("/apply/<int:company_id>", methods=["POST"])
@login_required("student")
def apply(company_id):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT cgpa FROM students WHERE student_id=%s", (session["student_id"],))
    student = cur.fetchone()
    cur.execute("SELECT eligibility_cgpa FROM companies WHERE company_id=%s", (company_id,))
    company = cur.fetchone()
    if not company:
        flash("Company not found.", "error")
    elif student["cgpa"] < float(company["eligibility_cgpa"]):
        flash("Your CGPA does not meet this company's eligibility criteria.", "error")
    else:
        try:
            cur.execute(
                "INSERT INTO applications (student_id, company_id, applied_date, round, status) VALUES (%s,%s,%s,%s,'Applied')",
                (session["student_id"], company_id, date.today(), "Application")
            )
            conn.commit()
            flash("Application submitted successfully.", "success")
        except Error:
            conn.rollback()
            flash("You have already applied for this company, or the application could not be saved.", "error")
    cur.close()
    conn.close()
    return redirect(url_for("student_portal"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    try:
        connection = get_db()
        connection.close()
        create_default_admin()
        print("MySQL connected. Default admin: admin / admin123")
        app.run(debug=True)
    except Error as e:
        print("Database connection failed:", e)
        print("Check MySQL is running and DB_CONFIG password is correct.")

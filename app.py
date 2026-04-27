from flask import Flask, render_template, request, redirect, session, flash
import mysql.connector
from flask_bcrypt import Bcrypt
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "secret123")
bcrypt = Bcrypt(app)

# ===============================
# DATABASE CONNECTION
# ===============================
def get_db():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST") or "shortline.proxy.rlwy.net",
        user=os.environ.get("DB_USER") or "root",
        password=os.environ.get("DB_PASSWORD") or "stBpgfzAqfqgzRRxGBNEFVDOFmAJgkDk",
        database=os.environ.get("DB_NAME") or "railway",
        port=int(os.environ.get("DB_PORT", "56205"))
    )

# ===============================
# HOME
# ===============================
@app.route("/")
def home():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT jobs.*, companies.company_name
        FROM jobs
        JOIN companies ON jobs.company_id = companies.id
        ORDER BY jobs.id DESC
    """)
    jobs = cursor.fetchall()

    return render_template("home.html", jobs=jobs)

# ===============================
# AUTH PAGES
# ===============================
@app.route("/login_page")
def login_page():
    return render_template("login.html")

@app.route("/register_page")
def register_page():
    return render_template("register.html")

@app.route("/company_register_page")
def company_register_page():
    return render_template("company_register.html")

# ===============================
# STUDENT REGISTER
# ===============================
@app.route("/register", methods=["POST"])
def register():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    email = request.form.get("email")

    cursor.execute("SELECT * FROM students WHERE email=%s", (email,))
    if cursor.fetchone():
        flash("Email already exists")
        return redirect("/register_page")

    password = bcrypt.generate_password_hash(request.form.get("password")).decode("utf-8")

    cursor.execute(
        "INSERT INTO students(name,email,password,course,mobile) VALUES(%s,%s,%s,%s,%s)",
        (
            request.form.get("name"),
            email,
            password,
            request.form.get("course"),
            request.form.get("mobile")
        )
    )
    db.commit()

    flash("Registered Successfully")
    return redirect("/login_page")

# ===============================
# STUDENT LOGIN
# ===============================
@app.route("/login", methods=["POST"])
def login():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM students WHERE email=%s", (request.form.get("email"),))
    user = cursor.fetchone()

    if user and bcrypt.check_password_hash(user["password"], request.form.get("password")):

        if user["is_blocked"]:
            return render_template("blocked.html")

        session["student_id"] = user["id"]
        session["student_name"] = user["name"]

        return redirect("/dashboard_student")

    flash("Invalid Login")
    return redirect("/login_page")

# ===============================
# STUDENT DASHBOARD
# ===============================
@app.route("/dashboard_student")
def dashboard_student():
    if "student_id" not in session:
        return redirect("/login_page")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM jobs ORDER BY id DESC")
    jobs = cursor.fetchall()

    cursor.execute("SELECT * FROM students WHERE id=%s", (session["student_id"],))
    student = cursor.fetchone()

    return render_template("dashboard_student.html", jobs=jobs, student=student)

# ===============================
# APPLY JOB
# ===============================
@app.route("/apply/<int:job_id>")
def apply(job_id):
    if "student_id" not in session:
        return redirect("/login_page")

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "INSERT INTO applications(student_id,job_id) VALUES(%s,%s)",
        (session["student_id"], job_id)
    )
    db.commit()

    flash("Applied Successfully")
    return redirect("/dashboard_student")

# ===============================
# PROFILE
# ===============================
@app.route("/profile")
def profile():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM students WHERE id=%s", (session["student_id"],))
    user = cursor.fetchone()

    return render_template("profile.html", user=user)

# ===============================
# MY APPLICATIONS
# ===============================
@app.route("/my_applications")
def my_applications():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT applications.*, jobs.title
        FROM applications
        JOIN jobs ON applications.job_id = jobs.id
        WHERE student_id=%s
    """, (session["student_id"],))

    apps = cursor.fetchall()

    return render_template("my_applications.html", apps=apps)

# ===============================
# COMPANY LOGIN
# ===============================
@app.route("/company_login", methods=["POST"])
def company_login():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM companies WHERE email=%s", (request.form.get("email"),))
    company = cursor.fetchone()

    if company and bcrypt.check_password_hash(company["password"], request.form.get("password")):
        session["company_id"] = company["id"]
        session["company_name"] = company["company_name"]
        return redirect("/company_dashboard")

    flash("Invalid Company Login")
    return redirect("/login_page")

# ===============================
# COMPANY DASHBOARD
# ===============================
@app.route("/company_dashboard")
def company_dashboard():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM jobs WHERE company_id=%s", (session["company_id"],))
    jobs = cursor.fetchall()

    return render_template("company_dashboard.html", jobs=jobs)

# ===============================
# POST JOB
# ===============================
@app.route("/post_job", methods=["POST"])
def post_job():
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "INSERT INTO jobs(company_id,title,description,salary,location,deadline) VALUES(%s,%s,%s,%s,%s,%s)",
        (
            session["company_id"],
            request.form.get("title"),
            request.form.get("description"),
            request.form.get("salary"),
            request.form.get("location"),
            request.form.get("deadline"),
        )
    )
    db.commit()

    return redirect("/company_dashboard")

# ===============================
# VIEW APPLICANTS
# ===============================
@app.route("/view_applicants/<int:job_id>")
def view_applicants(job_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT applications.id, students.name, students.email
        FROM applications
        JOIN students ON applications.student_id = students.id
        WHERE job_id=%s
    """, (job_id,))

    applicants = cursor.fetchall()

    return render_template("applicants.html", applicants=applicants)

# ===============================
# ADMIN LOGIN
# ===============================
@app.route("/admin_login", methods=["POST"])
def admin_login():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM admin WHERE username=%s AND password=%s",
        (request.form.get("username"), request.form.get("password"))
    )

    if cursor.fetchone():
        session["admin"] = True
        return redirect("/admin_dashboard")

    flash("Invalid Admin Login")
    return redirect("/login_page")

# ===============================
# ADMIN DASHBOARD
# ===============================
@app.route("/admin_dashboard")
def admin_dashboard():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total FROM students")
    students = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM companies")
    companies = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM jobs")
    jobs = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM applications")
    applications = cursor.fetchone()["total"]

    return render_template("admin_dashboard.html",
                           students=students,
                           companies=companies,
                           jobs=jobs,
                           applications=applications)

# ===============================
# ADMIN TABLES
# ===============================
@app.route("/admin_students")
def admin_students():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM students")
    data = cursor.fetchall()

    return render_template("admin_students.html", data=data)

@app.route("/admin_companies")
def admin_companies():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM companies")
    data = cursor.fetchall()

    return render_template("admin_companies.html", data=data)

@app.route("/admin_jobs")
def admin_jobs():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT jobs.*, companies.company_name
        FROM jobs
        JOIN companies ON jobs.company_id = companies.id
    """)
    data = cursor.fetchall()

    return render_template("admin_jobs.html", data=data)

@app.route("/admin_applications")
def admin_applications():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT applications.*, students.name, jobs.title
        FROM applications
        JOIN students ON applications.student_id = students.id
        JOIN jobs ON applications.job_id = jobs.id
    """)
    data = cursor.fetchall()

    return render_template("admin_applications.html", data=data)

# ===============================
# RUN
# ===============================
if __name__ == "__main__":
    app.run(debug=True)
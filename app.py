from flask import Flask, render_template, request, redirect, session, flash, send_file
import mysql.connector
from flask_bcrypt import Bcrypt
from functools import wraps
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from reportlab.pdfgen import canvas
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
bcrypt = Bcrypt(app)

# ===============================
# DATABASE CONNECTION
# ===============================
import os

db = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)

cursor = db.cursor(dictionary=True)

# ===============================
# EMAIL CONFIGURATION
# ===============================
EMAIL = os.getenv("EMAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

def send_email(to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL, EMAIL_PASSWORD)
        server.sendmail(EMAIL, to_email, msg.as_string())
        server.quit()
    except:
        print("Email failed")

# ===============================
# HOME PAGE
# ===============================
@app.route("/")
def home():
    cursor.execute("""
        SELECT jobs.*, companies.company_name
        FROM jobs
        JOIN companies ON jobs.company_id = companies.id
        ORDER BY jobs.id DESC
    """)
    jobs = cursor.fetchall()
    return render_template("home.html", jobs=jobs)

# ===============================
# LOGIN PAGES
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
    name = request.form["name"]
    email = request.form["email"]
    password = bcrypt.generate_password_hash(request.form["password"]).decode("utf-8")
    course = request.form["course"]
    mobile = request.form["mobile"]

    cursor.execute("SELECT * FROM students WHERE email=%s", (email,))
    user = cursor.fetchone()

    if user:
        flash("Email already exists")
        return redirect("/register_page")

    sql = """
    INSERT INTO students(name,email,password,course,mobile)
    VALUES(%s,%s,%s,%s,%s)
    """
    values = (name, email, password, course, mobile)
    cursor.execute(sql, values)
    db.commit()

    send_email(email, "Registration Success",
               f"Hello {name}, you are registered successfully.")

    flash("Registration successful")
    return redirect("/login_page")

# ===============================
# STUDENT LOGIN
# ===============================
@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["password"]

    cursor.execute("SELECT * FROM students WHERE email=%s", (email,))
    user = cursor.fetchone()

    if user and bcrypt.check_password_hash(user["password"], password):

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

    student_id = session["student_id"]

    cursor.execute(
        "SELECT * FROM applications WHERE student_id=%s AND job_id=%s",
        (student_id, job_id)
    )

    old = cursor.fetchone()

    if old:
        flash("Already Applied")
        return redirect("/dashboard_student")

    cursor.execute(
        "INSERT INTO applications(student_id,job_id) VALUES(%s,%s)",
        (student_id, job_id)
    )
    db.commit()

    cursor.execute("SELECT email,name FROM students WHERE id=%s", (student_id,))
    stu = cursor.fetchone()

    send_email(stu["email"], "Application Submitted",
               f"Hello {stu['name']}, your application submitted successfully.")

    flash("Applied Successfully")
    return redirect("/dashboard_student")

# ===============================
# MY APPLICATIONS
# ===============================
@app.route("/my_applications")
def my_applications():
    if "student_id" not in session:
        return redirect("/login_page")

    cursor.execute("""
        SELECT applications.*, jobs.title
        FROM applications
        JOIN jobs ON applications.job_id = jobs.id
        WHERE applications.student_id=%s
    """, (session["student_id"],))

    apps = cursor.fetchall()

    return render_template("my_applications.html", apps=apps)

# ===============================
# PROFILE
# ===============================
@app.route("/profile")
def profile():
    if "student_id" not in session:
        return redirect("/login_page")

    cursor.execute("SELECT * FROM students WHERE id=%s", (session["student_id"],))
    user = cursor.fetchone()

    return render_template("profile.html", user=user)

# ===============================
# LOGOUT
# ===============================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")
# ===============================
# company register
# ===============================
@app.route("/company_register", methods=["POST"])
def company_register():
    name = request.form["company_name"]
    email = request.form["email"]
    password = bcrypt.generate_password_hash(request.form["password"]).decode("utf-8")
    website = request.form["website"]
    location = request.form["location"]

    cursor.execute("SELECT * FROM companies WHERE email=%s", (email,))
    if cursor.fetchone():
        flash("Company already exists")
        return redirect("/login_page")

    cursor.execute(
        "INSERT INTO companies(company_name,email,password,website,location) VALUES(%s,%s,%s,%s,%s)",
        (name, email, password, website, location)
    )
    db.commit()

    send_email(email, "Company Registered", f"{name}, your company account is ready.")

    flash("Company Registered Successfully")
    return redirect("/login_page")
# ===============================
# company login
# ===============================
@app.route("/company_login", methods=["POST"])
def company_login():
    email = request.form["email"]
    password = request.form["password"]

    cursor.execute("SELECT * FROM companies WHERE email=%s", (email,))
    company = cursor.fetchone()

    if company and bcrypt.check_password_hash(company["password"], password):
        session["company_id"] = company["id"]
        session["company_name"] = company["company_name"]
        return redirect("/company_dashboard")

    flash("Invalid Company Login")
    return redirect("/login_page")
# ===============================
# company dashboard
# ===============================
@app.route("/company_dashboard")
def company_dashboard():
    if "company_id" not in session:
        return redirect("/login_page")

    cursor.execute("SELECT * FROM jobs WHERE company_id=%s", (session["company_id"],))
    jobs = cursor.fetchall()

    return render_template("company_dashboard.html", jobs=jobs)
# ===============================
# Post Job
# ===============================
@app.route("/post_job", methods=["POST"])
def post_job():
    if "company_id" not in session:
        return redirect("/login_page")

    title = request.form["title"]
    description = request.form["description"]
    salary = request.form["salary"]
    location = request.form["location"]
    deadline = request.form["deadline"]

    cursor.execute(
        "INSERT INTO jobs(company_id,title,description,salary,location,deadline) VALUES(%s,%s,%s,%s,%s,%s)",
        (session["company_id"], title, description, salary, location, deadline)
    )
    db.commit()

    flash("Job Posted Successfully")
    return redirect("/company_dashboard")
# ===============================
# View Applicants
# ===============================
@app.route("/view_applicants/<int:job_id>")
def view_applicants(job_id):
    cursor.execute("""
        SELECT applications.id, students.name, students.email
        FROM applications
        JOIN students ON applications.student_id = students.id
        WHERE applications.job_id=%s
    """, (job_id,))
    applicants = cursor.fetchall()

    return render_template("applicants.html", applicants=applicants, job_id=job_id)
# ===============================
# Schedule Interview
# ===============================
@app.route("/schedule/<int:app_id>", methods=["POST"])
def schedule(app_id):
    date = request.form["date"]
    mode = request.form["mode"]
    link = request.form["link"]

    cursor.execute(
        "INSERT INTO interviews(application_id,interview_date,mode,meeting_link) VALUES(%s,%s,%s,%s)",
        (app_id, date, mode, link)
    )

    cursor.execute("UPDATE applications SET status='Interview Scheduled' WHERE id=%s", (app_id,))
    db.commit()

    # send email
    cursor.execute("""
        SELECT students.email, students.name
        FROM applications
        JOIN students ON applications.student_id = students.id
        WHERE applications.id=%s
    """, (app_id,))
    stu = cursor.fetchone()

    send_email(stu["email"], "Interview Scheduled",
               f"Hello {stu['name']}, your interview is scheduled on {date}")

    return redirect("/company_dashboard")
# ===============================
#Select/Reject Applicant
# ===============================
@app.route("/result/<int:app_id>/<string:res>")
def result(app_id, res):

    cursor.execute("UPDATE applications SET status=%s WHERE id=%s", (res, app_id))

    cursor.execute("""
        SELECT students.email, students.name
        FROM applications
        JOIN students ON applications.student_id = students.id
        WHERE applications.id=%s
    """, (app_id,))
    stu = cursor.fetchone()

    send_email(stu["email"], f"Result: {res}",
               f"Hello {stu['name']}, your result is {res}")

    db.commit()
    return redirect("/company_dashboard")
# ===============================
# Penality System
# ===============================
@app.route("/mark_absent/<int:app_id>")
def mark_absent(app_id):

    cursor.execute("""
        SELECT student_id FROM applications WHERE id=%s
    """, (app_id,))
    stu = cursor.fetchone()

    student_id = stu["student_id"]

    cursor.execute("""
        UPDATE students 
        SET penalty_points = penalty_points + 1,
            warning_count = warning_count + 1
        WHERE id=%s
    """, (student_id,))

    # block if >3 warnings
    cursor.execute("""
        UPDATE students SET is_blocked=TRUE 
        WHERE id=%s AND warning_count >= 3
    """, (student_id,))

    db.commit()
    return redirect("/company_dashboard")
# ===============================
# Admin Login
# ===============================
@app.route("/admin_login", methods=["POST"])
def admin_login():
    username = request.form["username"]
    password = request.form["password"]

    cursor.execute("SELECT * FROM admin WHERE username=%s AND password=%s",
                   (username, password))
    admin = cursor.fetchone()

    if admin:
        session["admin"] = username
        return redirect("/admin_dashboard")

    flash("Invalid Admin Login")
    return redirect("/login_page")
# ===============================
# Admin Dashboard
# ===============================
@app.route("/admin_dashboard")
def admin_dashboard():

    if "admin" not in session:
        return redirect("/login_page")

    # counts
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
# Admin - View Students
# ===============================
@app.route("/admin_students")
def admin_students():

    cursor.execute("SELECT * FROM students")
    data = cursor.fetchall()

    return render_template("admin_students.html", data=data)
# ===============================
# Admin - View Companies
# ===============================
@app.route("/admin_companies")
def admin_companies():

    cursor.execute("SELECT * FROM companies")
    data = cursor.fetchall()

    return render_template("admin_companies.html", data=data)
# ===============================
# Admin - View Jobs
# ===============================
@app.route("/admin_jobs")
def admin_jobs():

    cursor.execute("""
        SELECT jobs.*, companies.company_name
        FROM jobs
        JOIN companies ON jobs.company_id = companies.id
    """)
    data = cursor.fetchall()

    return render_template("admin_jobs.html", data=data)
# ===============================
# Admin - View Applications
# ===============================
@app.route("/admin_applications")
def admin_applications():

    cursor.execute("""
        SELECT applications.*, students.name, jobs.title
        FROM applications
        JOIN students ON applications.student_id = students.id
        JOIN jobs ON applications.job_id = jobs.id
    """)
    data = cursor.fetchall()

    return render_template("admin_applications.html", data=data)
# ===============================
# Admin - block/Unblock Student
# ===============================
@app.route("/toggle_block/<int:id>")
def toggle_block(id):

    cursor.execute("SELECT is_blocked FROM students WHERE id=%s", (id,))
    user = cursor.fetchone()

    new_status = not user["is_blocked"]

    cursor.execute("UPDATE students SET is_blocked=%s WHERE id=%s",
                   (new_status, id))
    db.commit()

    return redirect("/admin_students")
# ===============================
# RUN
# ===============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
app.run(host="0.0.0.0", port=port)
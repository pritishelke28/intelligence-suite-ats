from flask import Flask, render_template, request, redirect, session, send_from_directory
import sqlite3, os
from parser import extract_text_from_pdf
from screening import calculate_score

app = Flask(__name__)
app.secret_key = "ats_secret_key"

UPLOAD_FOLDER = "resumes"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

KEYWORDS = ["python", "machine learning", "sql", "data analysis"]

# ---------------- DATABASE INIT ----------------
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT,
        last_name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    description TEXT,
    experience_level TEXT,
    skills TEXT,
    status TEXT DEFAULT 'Open',
    immediate_joiner TEXT DEFAULT 'No'
    )
    """)



    c.execute("""
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT,
    job_id INTEGER,
    resume TEXT,
    score INTEGER,
    status TEXT DEFAULT 'Pending',

    current_employer TEXT,
    start_date TEXT,
    end_date TEXT,
    currently_working TEXT,
    current_ctc TEXT,
    expected_ctc TEXT,
    notice_period TEXT,
    skills TEXT,

    applied_date TEXT DEFAULT CURRENT_TIMESTAMP
)
""")



    # default admin
    c.execute("""
    INSERT OR IGNORE INTO users (email, password, role)
    VALUES ('admin@company.com', 'admin123', 'admin')
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- PUBLIC ----------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/careers")
def careers():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM jobs")
    jobs = c.fetchall()
    conn.close()
    return render_template("careers.html", jobs=jobs)

# ---------------- USER REGISTER ----------------
@app.route("/user-register", methods=["GET", "POST"])
def user_register():
    if request.method == "POST":
        fn = request.form["first_name"]
        ln = request.form["last_name"]
        email = request.form["email"]
        pw = request.form["password"]
        cpw = request.form["confirm_password"]

        if pw != cpw:
            return render_template("user_register.html", error="Passwords do not match")

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        try:
            c.execute("""
            INSERT INTO users (first_name, last_name, email, password, role)
            VALUES (?, ?, ?, ?, 'user')
            """, (fn, ln, email, pw))
            conn.commit()
        except:
            conn.close()
            return render_template("user_register.html", error="User already exists")

        conn.close()
        session["user"] = email
        session["first_name"] = fn
        return redirect("/")

    return render_template("user_register.html")

# ---------------- USER LOGIN ----------------
@app.route("/user-login", methods=["GET", "POST"])
def user_login():
    next_page = request.args.get("next")
    if request.method == "POST":
        email = request.form["email"]
        pw = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("""
        SELECT first_name FROM users
        WHERE email=? AND password=? AND role='user'
        """, (email, pw))
        user = c.fetchone()
        conn.close()

        if user:
            session["user"] = email
            session["first_name"] = user[0]
            return redirect(next_page or "/")

        return render_template("user_login.html", error="Invalid credentials")

    return render_template("user_login.html")

# ---------------- APPLY ----------------
@app.route("/apply/<int:job_id>", methods=["GET", "POST"])
def apply(job_id):
    if "user" not in session:
        return redirect(f"/user-login?next=/apply/{job_id}")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # Fetch job description
    c.execute("SELECT description, skills FROM jobs WHERE id=?", (job_id,))
    job = c.fetchone()

    if not job:
        conn.close()
        return "Job not found"

    job_description = job[0]
    job_skills = job[1] if job[1] else ""

    combined_jd = job_description + " " + job_skills

    if request.method == "POST":
        current_employer = request.form.get("current_employer")
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        currently_working = "Yes" if request.form.get("currently_working") else "No"
        current_ctc = request.form.get("current_ctc")
        expected_ctc = request.form.get("expected_ctc")
        notice_period = request.form.get("notice_period")
        skills = request.form.get("skills")
        
        file = request.files["resume"]
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)
        
        resume_text = extract_text_from_pdf(file_path)
        score = calculate_score(resume_text, combined_jd)
        c.execute("""
                  INSERT INTO applications (
                  user_email, job_id, resume, score,
                  current_employer, start_date, end_date,
                  currently_working, current_ctc,
                  expected_ctc, notice_period, skills
                  )
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                  """, (
                      session["user"], job_id, file.filename, score,
                      current_employer, start_date, end_date,
                      currently_working, current_ctc,
                      expected_ctc, notice_period, skills
                      ))
        
        conn.commit()
        conn.close()
        return redirect("/user-dashboard")

    conn.close()
    return render_template("apply.html", job=job)

# ---------------- USER DASHBOARD ----------------
@app.route("/user-dashboard")
def user_dashboard():
    if "user" not in session:
        return redirect("/user-login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
    SELECT 
        applications.id,
        jobs.title,
        applications.status,
        applications.applied_date
    FROM applications
    JOIN jobs ON applications.job_id = jobs.id
    WHERE applications.user_email=?
    ORDER BY applications.applied_date DESC
    """, (session["user"],))

    applications = c.fetchall()
    conn.close()

    return render_template("user_dashboard.html", applications=applications)



@app.route("/application-overview/<int:app_id>")
def application_overview(app_id):
    if "user" not in session:
        return redirect("/user-login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
    SELECT applications.*, jobs.title, jobs.skills
    FROM applications
    JOIN jobs ON applications.job_id = jobs.id
    WHERE applications.id=? AND applications.user_email=?
    """, (app_id, session["user"]))

    application = c.fetchone()
    conn.close()

    if not application:
        return "Application not found"

    # ---------------- Skill Comparison Logic ----------------

    applicant_skills = application[13] or ""
    job_skills = application[-1] or ""  # last column from SELECT

    applicant_list = [s.strip().lower() for s in applicant_skills.split(",") if s.strip()]
    job_list = [s.strip().lower() for s in job_skills.split(",") if s.strip()]

    matching = list(set(applicant_list) & set(job_list))
    missing = list(set(job_list) - set(applicant_list))
    irrelevant = list(set(applicant_list) - set(job_list))

    return render_template(
        "application_overview.html",
        app=application,
        matching=matching,
        missing=missing,
        irrelevant=irrelevant
    )




# ---------------- ADMIN LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form["email"]
        pw = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT role FROM users WHERE email=? AND password=?", (email, pw))
        user = c.fetchone()
        conn.close()

        if user and user[0] == "admin":
            session["admin"] = True
            return redirect("/admin")

        return render_template("login.html", error="Invalid admin login")

    return render_template("login.html")

# ---------------- ADMIN DASHBOARD ----------------
@app.route("/admin")
def admin_dashboard():
    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""
        SELECT jobs.id,
        jobs.title,
        jobs.status,
        COUNT(applications.id) as total_applicants
        FROM jobs
        LEFT JOIN applications ON jobs.id = applications.job_id
        GROUP BY jobs.id
        """)

    jobs = c.fetchall()
    conn.close()

    return render_template("admin_dashboard.html", jobs=jobs)

# ---------------- ADD JOB ----------------
@app.route("/add-job", methods=["GET", "POST"])
def add_job():
    if not session.get("admin"):
        return redirect("/login")

    if request.method == "POST":
        title = request.form["title"]
        desc = request.form["description"]
        experience = request.form["experience_level"]
        skills = request.form["skills"]  # ✅ NEW
        immediate_joiner = "Yes" if request.form.get("immediate_joiner") else "No"

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("""
        INSERT INTO jobs (title, description, experience_level, skills, immediate_joiner)
        VALUES (?, ?, ?, ?, ?)
        """, (title, desc, experience, skills, immediate_joiner))

        conn.commit()
        conn.close()

        return redirect("/admin")

    return render_template("add_job.html")



# ---------------- EDIT / CLOSE JOB ----------------
@app.route("/edit-job/<int:job_id>", methods=["GET", "POST"])
def edit_job(job_id):
    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        experience = request.form["experience_level"]
        skills = request.form["skills"]   # ✅ NEW
        immediate_joiner = "Yes" if request.form.get("immediate_joiner") else "No"

        c.execute("""
        UPDATE jobs
        SET title=?, description=?, experience_level=?, skills=?, immediate_joiner=?
        WHERE id=?
        """, (title, description, experience, skills, immediate_joiner, job_id))


    # GET request
    c.execute("SELECT * FROM jobs WHERE id=?", (job_id,))
    job = c.fetchone()
    conn.close()

    return render_template("edit_job.html", job=job)



@app.route("/admin/job-details/<int:job_id>")
def job_details(job_id):
    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # Job data
    c.execute("SELECT * FROM jobs WHERE id=?", (job_id,))
    job = c.fetchone()

    # Total applicants
    c.execute("SELECT COUNT(*) FROM applications WHERE job_id=?", (job_id,))
    total_applicants = c.fetchone()[0]

    conn.close()

    return render_template(
        "job_details.html",
        job=job,
        total_applicants=total_applicants
    )

@app.route("/close-job/<int:job_id>")
def close_job(job_id):
    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("UPDATE jobs SET status='Closed' WHERE id=?", (job_id,))
    conn.commit()
    conn.close()

    return redirect(f"/admin/job-details/{job_id}")


@app.route("/reopen-job/<int:job_id>")
def reopen_job(job_id):
    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("UPDATE jobs SET status='Open' WHERE id=?", (job_id,))
    conn.commit()
    conn.close()

    return redirect(f"/admin/job-details/{job_id}")




# ---------------- VIEW APPLICANTS ----------------
@app.route("/admin/job/<int:job_id>")
def job_applicants(job_id):
    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
    SELECT applications.id,
           users.first_name,
           users.last_name,
           applications.score,
           applications.status
    FROM applications
    JOIN users ON applications.user_email = users.email
    WHERE applications.job_id=?
    """, (job_id,))

    applicants = c.fetchall()
    conn.close()

    return render_template("job_applicants.html", applicants=applicants)


@app.route("/admin/view-application/<int:app_id>")
def admin_view_application(app_id):
    if "admin" not in session:
        return redirect("/admin-login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
        SELECT applications.*, jobs.title, jobs.skills
        FROM applications
        JOIN jobs ON applications.job_id = jobs.id
        WHERE applications.id=?
    """, (app_id,))

    application = c.fetchone()
    conn.close()

    if not application:
        return "Application not found"

    return render_template("admin_view_application.html", app=application)




# ---------------- SHORTLIST / REJECT ----------------
@app.route("/update-status/<int:app_id>/<status>")
def update_status(app_id, status):
    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""
    UPDATE applications SET status=? WHERE id=?
    """, (status, app_id))
    conn.commit()
    conn.close()

    return redirect(request.referrer)


# ---------------- VIEW RESUME ----------------
@app.route("/resumes/<filename>")
def view_resume(filename):
    return send_from_directory("resumes", filename)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)

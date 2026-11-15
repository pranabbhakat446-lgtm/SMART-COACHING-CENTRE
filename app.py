
import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db, init_db

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

if not app.secret_key:
    raise RuntimeError("SECRET_KEY .env file mein set kijiye.")


def create_admin():
    username = os.getenv("ADMIN_USERNAME")
    password = os.getenv("ADMIN_PASSWORD")

    if not username or not password:
        raise RuntimeError("ADMIN_USERNAME aur ADMIN_PASSWORD .env mein set kijiye.")

    conn = get_db()
    admin = conn.execute(
        "SELECT id FROM admin WHERE username = ?", (username,)
    ).fetchone()

    if not admin:
        conn.execute(
            "INSERT INTO admin (username, password_hash) VALUES (?, ?)",
            (username, generate_password_hash(password))
        )
        conn.commit()

    conn.close()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        qualification = request.form.get("qualification", "").strip()
        coaching_for = request.form.get("coaching_for", "").strip()
        phone = request.form.get("phone", "").strip()

        if not name or not qualification or not coaching_for:
            flash("Please fill all required fields.", "error")
            return redirect(url_for("register"))

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            """INSERT INTO students
               (name, qualification, coaching_for, phone)
               VALUES (?, ?, ?, ?)""",
            (name, qualification, coaching_for, phone)
        )

        student_id = cursor.lastrowid
        student_code = f"{student_id:02d}"

        cursor.execute(
            "UPDATE students SET student_code = ? WHERE id = ?",
            (student_code, student_id)
        )

        conn.commit()
        conn.close()

        return render_template(
            "success.html",
            student_code=student_code,
            student_name=name
        )

    return render_template("register.html")


@app.route("/career", methods=["GET", "POST"])
def career():
    if request.method == "POST":
        student_name = request.form.get("student_name", "").strip()
        contact = request.form.get("contact", "").strip()
        question = request.form.get("question", "").strip()

        if not student_name or not question:
            flash("Please enter your name and question.", "error")
            return redirect(url_for("career"))

        conn = get_db()
        conn.execute(
            """INSERT INTO career_requests
               (student_name, contact, question)
               VALUES (?, ?, ?)""",
            (student_name, contact, question)
        )
        conn.commit()
        conn.close()

        flash("Your career question has been submitted.", "success")
        return redirect(url_for("career"))

    return render_template("career.html")


@app.route("/problem", methods=["GET", "POST"])
def problem():
    if request.method == "POST":
        student_name = request.form.get("student_name", "").strip()
        student_code = request.form.get("student_code", "").strip()
        category = request.form.get("category", "").strip()
        message = request.form.get("message", "").strip()

        if not student_name or not category or not message:
            flash("Please fill all required fields.", "error")
            return redirect(url_for("problem"))

        conn = get_db()
        conn.execute(
            """INSERT INTO problems
               (student_name, student_code, category, message)
               VALUES (?, ?, ?, ?)""",
            (student_name, student_code, category, message)
        )
        conn.commit()
        conn.close()

        flash("Your problem has been submitted.", "success")
        return redirect(url_for("problem"))

    return render_template("problem.html")



@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()
        message = request.form.get("message", "").strip()

        if not name or not phone or not message:
            flash("Please fill all required fields.", "error")
            return redirect(url_for("contact"))

        conn = get_db()
        conn.execute(
            """INSERT INTO contact_messages
               (name, phone, email, message)
               VALUES (?, ?, ?, ?)""",
            (name, phone, email, message)
        )
        conn.commit()
        conn.close()

        flash("Your message has been sent successfully!", "success")
        return redirect(url_for("contact"))

    return render_template("contact.html")


@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_db()
        admin = conn.execute(
            "SELECT * FROM admin WHERE username = ?", (username,)
        ).fetchone()
        conn.close()

        if admin and check_password_hash(admin["password_hash"], password):
            session["admin_id"] = admin["id"]
            session["admin_username"] = admin["username"]
            return redirect(url_for("dashboard"))

        flash("Invalid username or password.", "error")

    return render_template("admin_login.html")


@app.route("/admin-logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


@app.route("/admin-dashboard")
def dashboard():
    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    conn = get_db()

    total_students = conn.execute(
        "SELECT COUNT(*) FROM students"
    ).fetchone()[0]

    total_career = conn.execute(
        "SELECT COUNT(*) FROM career_requests"
    ).fetchone()[0]

    total_problems = conn.execute(
        "SELECT COUNT(*) FROM problems"
    ).fetchone()[0]

    pending_problems = conn.execute(
        "SELECT COUNT(*) FROM problems WHERE status = 'Pending'"
    ).fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        total_students=total_students,
        total_career=total_career,
        total_problems=total_problems,
        pending_problems=pending_problems
    )


@app.route("/admin/students")
def students():
    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    search = request.args.get("search", "").strip()

    conn = get_db()

    if search:
        records = conn.execute(
            """SELECT * FROM students
               WHERE name LIKE ? OR student_code LIKE ?
               ORDER BY id DESC""",
            (f"%{search}%", f"%{search}%")
        ).fetchall()
    else:
        records = conn.execute(
            "SELECT * FROM students ORDER BY id DESC"
        ).fetchall()

    conn.close()
    return render_template("students.html", students=records, search=search)


@app.route("/admin/student/<int:student_id>")
def student_details(student_id):
    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    conn = get_db()
    student = conn.execute(
        "SELECT * FROM students WHERE id = ?", (student_id,)
    ).fetchone()
    conn.close()

    if not student:
        flash("Student not found.", "error")
        return redirect(url_for("students"))

    return render_template("student_details.html", student=student)


@app.route("/admin/edit-student/<int:student_id>", methods=["GET", "POST"])
def edit_student(student_id):
    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    conn = get_db()

    student = conn.execute(
        "SELECT * FROM students WHERE id = ?", (student_id,)
    ).fetchone()

    if not student:
        conn.close()
        flash("Student not found.", "error")
        return redirect(url_for("students"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        qualification = request.form.get("qualification", "").strip()
        coaching_for = request.form.get("coaching_for", "").strip()
        phone = request.form.get("phone", "").strip()

        if not name or not qualification or not coaching_for:
            flash("Please fill all required fields.", "error")
            conn.close()
            return redirect(url_for("edit_student", student_id=student_id))

        conn.execute(
            """UPDATE students
               SET name = ?, qualification = ?, coaching_for = ?, phone = ?
               WHERE id = ?""",
            (name, qualification, coaching_for, phone, student_id)
        )
        conn.commit()
        conn.close()

        flash("Student details updated.", "success")
        return redirect(url_for("student_details", student_id=student_id))

    conn.close()
    return render_template("edit_student.html", student=student)


@app.route("/admin/delete-student/<int:student_id>", methods=["POST"])
def delete_student(student_id):
    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    conn = get_db()
    conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
    conn.commit()
    conn.close()

    flash("Student record deleted.", "success")
    return redirect(url_for("students"))


@app.route("/admin/career-requests")
def career_requests():
    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    conn = get_db()
    requests_list = conn.execute(
        "SELECT * FROM career_requests ORDER BY id DESC"
    ).fetchall()
    conn.close()

    return render_template(
        "career_requests.html",
        requests_list=requests_list
    )


@app.route("/admin/problems")
def problems():
    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    conn = get_db()
    problems_list = conn.execute(
        "SELECT * FROM problems ORDER BY id DESC"
    ).fetchall()
    conn.close()

    return render_template("problems.html", problems=problems_list)


@app.route("/admin/update-problem/<int:problem_id>", methods=["POST"])
def update_problem(problem_id):
    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    status = request.form.get("status", "").strip()
    admin_reply = request.form.get("admin_reply", "").strip()

    allowed_statuses = ["Pending", "In Progress", "Solved"]

    if status not in allowed_statuses:
        flash("Invalid problem status.", "error")
        return redirect(url_for("problems"))

    conn = get_db()

    conn.execute(
        """UPDATE problems
           SET status = ?, admin_reply = ?
           WHERE id = ?""",
        (status, admin_reply, problem_id)
    )

    conn.commit()
    conn.close()

    flash("Problem updated successfully!", "success")
    return redirect(url_for("problems"))


@app.route("/admin/reply-career/<int:request_id>", methods=["POST"])
def reply_career(request_id):
    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    status = request.form.get("status", "").strip()
    response = request.form.get("response", "").strip()

    allowed_statuses = ["Pending", "In Progress", "Solved"]

    if status not in allowed_statuses:
        flash("Invalid career request status.", "error")
        return redirect(url_for("career_requests"))

    conn = get_db()

    conn.execute(
        """UPDATE career_requests
           SET status = ?, response = ?
           WHERE id = ?""",
        (status, response, request_id)
    )

    conn.commit()
    conn.close()

    flash("Career reply saved successfully!", "success")
    return redirect(url_for("career_requests"))


@app.route("/admin/contact-messages")
def contact_messages():
    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    conn = get_db()

    messages_list = conn.execute(
        "SELECT * FROM contact_messages ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template(
        "contact_messages.html",
        messages_list=messages_list
    )


if __name__ == "__main__":
    init_db()
    create_admin()
    app.run(debug=True)

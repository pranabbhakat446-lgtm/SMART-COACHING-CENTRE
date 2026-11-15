
import os
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, flash, session
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

from database import get_db, init_db

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

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
    try:
        existing = conn.execute(
            "SELECT id FROM admin WHERE username = %s",
            (username,)
        ).fetchone()

        if not existing:
            conn.execute(
                "INSERT INTO admin (username, password_hash) VALUES (%s, %s)",
                (username, generate_password_hash(password))
            )
            conn.commit()
    finally:
        conn.close()


def admin_required():
    return "admin_id" in session


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
        try:
            student = conn.execute(
                """
                INSERT INTO students
                (name, qualification, coaching_for, phone)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (name, qualification, coaching_for, phone)
            ).fetchone()

            student_id = student["id"]
            student_code = f"{student_id:02d}"

            conn.execute(
                "UPDATE students SET student_code = %s WHERE id = %s",
                (student_code, student_id)
            )
            conn.commit()
        finally:
            conn.close()

        return render_template(
            "success.html",
            student_code=student_code,
            name=name
        )

    return render_template("register.html")


@app.route("/career", methods=["GET", "POST"])
def career():
    if request.method == "POST":
        student_name = request.form.get("student_name", "").strip()
        contact = request.form.get("contact", "").strip()
        question = request.form.get("question", "").strip()

        if not student_name or not question:
            flash("Please fill all required fields.", "error")
            return redirect(url_for("career"))

        conn = get_db()
        try:
            conn.execute(
                """
                INSERT INTO career_requests
                (student_name, contact, question)
                VALUES (%s, %s, %s)
                """,
                (student_name, contact, question)
            )
            conn.commit()
        finally:
            conn.close()

        flash("Your career guidance request has been submitted.", "success")
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
        try:
            conn.execute(
                """
                INSERT INTO problems
                (student_name, student_code, category, message)
                VALUES (%s, %s, %s, %s)
                """,
                (student_name, student_code, category, message)
            )
            conn.commit()
        finally:
            conn.close()

        flash("Your problem has been submitted successfully.", "success")
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
        try:
            conn.execute(
                """
                INSERT INTO contact_messages
                (name, phone, email, message)
                VALUES (%s, %s, %s, %s)
                """,
                (name, phone, email, message)
            )
            conn.commit()
        finally:
            conn.close()

        flash("Your message has been sent successfully.", "success")
        return redirect(url_for("contact"))

    return render_template("contact.html")


@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_db()
        try:
            admin = conn.execute(
                "SELECT * FROM admin WHERE username = %s",
                (username,)
            ).fetchone()
        finally:
            conn.close()

        if admin and check_password_hash(admin["password_hash"], password):
            session["admin_id"] = admin["id"]
            session["admin_username"] = admin["username"]
            return redirect(url_for("admin_dashboard"))

        flash("Invalid username or password.", "error")

    return render_template("admin_login.html")


@app.route("/admin-logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


@app.route("/admin-dashboard")
def admin_dashboard():
    if not admin_required():
        return redirect(url_for("admin_login"))

    conn = get_db()
    try:
        students_count = conn.execute(
            "SELECT COUNT(*) AS total FROM students"
        ).fetchone()["total"]

        career_count = conn.execute(
            "SELECT COUNT(*) AS total FROM career_requests"
        ).fetchone()["total"]

        problems_count = conn.execute(
            "SELECT COUNT(*) AS total FROM problems"
        ).fetchone()["total"]

        pending_problems = conn.execute(
            "SELECT COUNT(*) AS total FROM problems WHERE status = %s",
            ("Pending",)
        ).fetchone()["total"]
    finally:
        conn.close()

    return render_template(
        "dashboard.html",
        students_count=students_count,
        career_count=career_count,
        problems_count=problems_count,
        pending_problems=pending_problems
    )


@app.route("/admin/students")
def admin_students():
    if not admin_required():
        return redirect(url_for("admin_login"))

    search = request.args.get("search", "").strip()

    conn = get_db()
    try:
        students = conn.execute(
            """
            SELECT * FROM students
            WHERE name ILIKE %s OR student_code ILIKE %s
            ORDER BY id DESC
            """,
            (f"%{search}%", f"%{search}%")
        ).fetchall()
    finally:
        conn.close()

    return render_template("students.html", students=students, search=search)


@app.route("/admin/student/<int:student_id>")
def student_details(student_id):
    if not admin_required():
        return redirect(url_for("admin_login"))

    conn = get_db()
    try:
        student = conn.execute(
            "SELECT * FROM students WHERE id = %s",
            (student_id,)
        ).fetchone()
    finally:
        conn.close()

    if not student:
        flash("Student not found.", "error")
        return redirect(url_for("admin_students"))

    return render_template("student_details.html", student=student)


@app.route("/admin/edit-student/<int:student_id>", methods=["GET", "POST"])
def edit_student(student_id):
    if not admin_required():
        return redirect(url_for("admin_login"))

    conn = get_db()
    try:
        student = conn.execute(
            "SELECT * FROM students WHERE id = %s",
            (student_id,)
        ).fetchone()

        if not student:
            flash("Student not found.", "error")
            return redirect(url_for("admin_students"))

        if request.method == "POST":
            name = request.form.get("name", "").strip()
            qualification = request.form.get("qualification", "").strip()
            coaching_for = request.form.get("coaching_for", "").strip()
            phone = request.form.get("phone", "").strip()

            conn.execute(
                """
                UPDATE students
                SET name = %s, qualification = %s,
                    coaching_for = %s, phone = %s
                WHERE id = %s
                """,
                (name, qualification, coaching_for, phone, student_id)
            )
            conn.commit()

            flash("Student details updated successfully.", "success")
            return redirect(url_for("student_details", student_id=student_id))
    finally:
        conn.close()

    return render_template("edit_student.html", student=student)


@app.route("/admin/delete-student/<int:student_id>", methods=["POST"])
def delete_student(student_id):
    if not admin_required():
        return redirect(url_for("admin_login"))

    conn = get_db()
    try:
        conn.execute(
            "DELETE FROM students WHERE id = %s",
            (student_id,)
        )
        conn.commit()
    finally:
        conn.close()

    flash("Student deleted successfully.", "success")
    return redirect(url_for("admin_students"))


@app.route("/admin/career-requests")
def career_requests():
    if not admin_required():
        return redirect(url_for("admin_login"))

    conn = get_db()
    try:
        requests_list = conn.execute(
            "SELECT * FROM career_requests ORDER BY id DESC"
        ).fetchall()
    finally:
        conn.close()

    return render_template("career_requests.html", requests=requests_list)


@app.route("/admin/problems")
def admin_problems():
    if not admin_required():
        return redirect(url_for("admin_login"))

    conn = get_db()
    try:
        problems_list = conn.execute(
            "SELECT * FROM problems ORDER BY id DESC"
        ).fetchall()
    finally:
        conn.close()

    return render_template("problems.html", problems=problems_list)


@app.route("/admin/update-problem/<int:problem_id>", methods=["POST"])
def update_problem(problem_id):
    if not admin_required():
        return redirect(url_for("admin_login"))

    status = request.form.get("status", "Pending")
    admin_reply = request.form.get("admin_reply", "").strip()

    if status not in ["Pending", "In Progress", "Solved"]:
        status = "Pending"

    conn = get_db()
    try:
        conn.execute(
            """
            UPDATE problems
            SET status = %s, admin_reply = %s
            WHERE id = %s
            """,
            (status, admin_reply, problem_id)
        )
        conn.commit()
    finally:
        conn.close()

    flash("Problem updated successfully.", "success")
    return redirect(url_for("admin_problems"))


@app.route("/admin/reply-career/<int:request_id>", methods=["POST"])
def reply_career(request_id):
    if not admin_required():
        return redirect(url_for("admin_login"))

    response = request.form.get("response", "").strip()
    status = request.form.get("status", "Pending")

    conn = get_db()
    try:
        conn.execute(
            """
            UPDATE career_requests
            SET response = %s, status = %s
            WHERE id = %s
            """,
            (response, status, request_id)
        )
        conn.commit()
    finally:
        conn.close()

    flash("Career request updated successfully.", "success")
    return redirect(url_for("career_requests"))


@app.route("/admin/contact-messages")
def contact_messages():
    if not admin_required():
        return redirect(url_for("admin_login"))

    conn = get_db()
    try:
        messages = conn.execute(
            "SELECT * FROM contact_messages ORDER BY id DESC"
        ).fetchall()
    finally:
        conn.close()

    return render_template("contact_messages.html", messages=messages)


if __name__ == "__main__":
    init_db()
    create_admin()
    app.run(debug=True)

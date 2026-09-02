from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime, timedelta
import uuid
import os

from ai.ai_engine import analyze_complaint


app = Flask(__name__)

app.secret_key = "civicai-demo-secret"

DATABASE = "civicai.db"

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db_connection():

    connection = sqlite3.connect(DATABASE)

    connection.row_factory = sqlite3.Row

    return connection


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return redirect(url_for("login"))


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET"])
def login():

    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login_user():

    email = request.form["email"].strip()

    password = request.form["password"]

    role = request.form["role"]


    connection = get_db_connection()


    user = connection.execute(
        """
        SELECT *
        FROM users
        WHERE email = ?
        AND password = ?
        AND role = ?
        """,
        (email, password, role)
    ).fetchone()


    connection.close()


    if user is None:

        return "Invalid email, password, or role"


    session["user_id"] = user["id"]

    session["name"] = user["name"]

    session["email"] = user["email"]

    session["role"] = user["role"]


    # ADMIN LOGIN
    if user["role"] == "admin":

        return redirect(url_for("admin_dashboard"))


    # CITIZEN LOGIN
    return redirect(url_for("user_dashboard"))


# =========================================================
# SIGNUP
# =========================================================

@app.route("/signup", methods=["GET"])
def signup():

    # Get role from URL
    # Example:
    # /signup?role=user
    # /signup?role=admin

    role = request.args.get("role", "user")


    # Only allow user or admin
    if role not in ["user", "admin"]:

        role = "user"


    return render_template(
        "signup.html",
        role=role
    )


@app.route("/signup", methods=["POST"])
def signup_user():

    name = request.form["name"].strip()

    email = request.form["email"].strip()

    password = request.form["password"]

    confirm_password = request.form["confirm_password"]

    role = request.form["role"]


    # Make sure role is valid

    if role not in ["user", "admin"]:

        return "Invalid account type"


    # Check passwords

    if password != confirm_password:

        return "Passwords do not match"


    connection = get_db_connection()


    # Check whether email already exists

    existing_user = connection.execute(
        """
        SELECT id
        FROM users
        WHERE email = ?
        """,
        (email,)
    ).fetchone()


    if existing_user:

        connection.close()

        return "Email already registered"


    # Create account with selected role

    connection.execute(
        """
        INSERT INTO users
        (
            name,
            email,
            password,
            role
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            name,
            email,
            password,
            role
        )
    )


    connection.commit()

    connection.close()


    # After signup go to login

    return redirect(url_for("login"))


# =========================================================
# USER DASHBOARD
# =========================================================

@app.route("/user-dashboard")
def user_dashboard():

    if session.get("role") != "user":

        return redirect(url_for("login"))


    connection = get_db_connection()


    complaints = connection.execute(
        """
        SELECT *
        FROM complaints
        WHERE citizen_name = ?
        ORDER BY id DESC
        """,
        (session["name"],)
    ).fetchall()


    connection.close()


    return render_template(
        "user_dashboard.html",
        complaints=complaints
    )


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin-dashboard")
def admin_dashboard():

    if session.get("role") != "admin":

        return redirect(url_for("login"))


    connection = get_db_connection()


    complaints = connection.execute(
        """
        SELECT *
        FROM complaints
        ORDER BY id DESC
        """
    ).fetchall()


    connection.close()


    return render_template(
        "admin_dashboard.html",
        complaints=complaints
    )


# =========================================================
# TEXT REPORT PAGE
# =========================================================

@app.route("/report")
def report():

    if session.get("role") != "user":

        return redirect(url_for("login"))


    return render_template(
        "report.html",
        name=session.get("name"),
        email=session.get("email")
    )


# =========================================================
# SUBMIT TEXT COMPLAINT
# =========================================================

@app.route("/submit-complaint", methods=["POST"])
def submit_complaint():

    if session.get("role") != "user":

        return redirect(url_for("login"))


    name = session["name"]

    phone = request.form["phone"].strip()

    description = request.form["description"].strip()

    location = request.form["location"].strip()


    complaint_id = "CIV-" + str(uuid.uuid4())[:8].upper()


    # AI ANALYSIS

    ai_result = analyze_complaint(description)


    category = ai_result["category"]

    priority = ai_result["priority"]

    department = ai_result["department"]

    ai_confidence = ai_result["confidence"]

    sla_hours = ai_result["sla_hours"]


    created_at = datetime.now()


    sla_deadline = created_at + timedelta(
        hours=sla_hours
    )


    status = "Submitted"


    # Optional image

    image = request.files.get("photo")

    image_path = ""


    if image and image.filename:

        filename = complaint_id + "_" + image.filename


        image_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )


        image.save(image_path)


    connection = get_db_connection()


    connection.execute(
        """
        INSERT INTO complaints
        (
            complaint_id,
            citizen_name,
            phone,
            description,
            category,
            priority,
            department,
            location,
            status,
            source,
            created_at,
            sla_deadline,
            ai_confidence,
            image_path
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            complaint_id,
            name,
            phone,
            description,
            category,
            priority,
            department,
            location,
            status,
            "Website",
            created_at.strftime("%Y-%m-%d %H:%M:%S"),
            sla_deadline.strftime("%Y-%m-%d %H:%M:%S"),
            ai_confidence,
            image_path
        )
    )


    connection.commit()

    connection.close()


    return render_template(
        "success.html",
        complaint_id=complaint_id,
        category=category,
        priority=priority,
        department=department,
        confidence=ai_confidence,
        sla_hours=sla_hours,
        status=status
    )


# =========================================================
# IMAGE REPORT PAGE
# =========================================================

@app.route("/image-report")
def image_report():

    if session.get("role") != "user":

        return redirect(url_for("login"))


    return render_template("image_report.html")


# =========================================================
# SUBMIT IMAGE COMPLAINT
# =========================================================

@app.route("/submit-image-complaint", methods=["POST"])
def submit_image_complaint():

    if session.get("role") != "user":

        return redirect(url_for("login"))


    image = request.files.get("image")


    if not image or image.filename == "":

        return "Please select an image"


    complaint_id = "CIV-" + str(uuid.uuid4())[:8].upper()


    filename = complaint_id + "_" + image.filename


    image_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )


    image.save(image_path)


    created_at = datetime.now()


    category = "Pending Image AI Analysis"

    priority = "Pending"

    department = "Pending"

    status = "Submitted"

    ai_confidence = 0.0

    sla_hours = 48


    sla_deadline = created_at + timedelta(
        hours=sla_hours
    )


    connection = get_db_connection()


    connection.execute(
        """
        INSERT INTO complaints
        (
            complaint_id,
            citizen_name,
            phone,
            description,
            category,
            priority,
            department,
            location,
            status,
            source,
            created_at,
            sla_deadline,
            ai_confidence,
            image_path
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            complaint_id,
            session["name"],
            "",
            "Complaint submitted through image",
            category,
            priority,
            department,
            "Not provided",
            status,
            "Image",
            created_at.strftime("%Y-%m-%d %H:%M:%S"),
            sla_deadline.strftime("%Y-%m-%d %H:%M:%S"),
            ai_confidence,
            image_path
        )
    )


    connection.commit()

    connection.close()


    return render_template(
        "success.html",
        complaint_id=complaint_id,
        category=category,
        priority=priority,
        department=department,
        confidence=ai_confidence,
        sla_hours=sla_hours,
        status=status
    )


# =========================================================
# TRACK PAGE
# =========================================================

@app.route("/track")
def track():

    if session.get("role") != "user":

        return redirect(url_for("login"))


    return render_template("track.html")


# =========================================================
# TRACK COMPLAINT
# =========================================================

@app.route("/track-complaint", methods=["POST"])
def track_complaint():

    if session.get("role") != "user":

        return redirect(url_for("login"))


    complaint_id = request.form["complaint_id"].strip()


    connection = get_db_connection()


    complaint = connection.execute(
        """
        SELECT *
        FROM complaints
        WHERE complaint_id = ?
        AND citizen_name = ?
        """,
        (
            complaint_id,
            session["name"]
        )
    ).fetchone()


    connection.close()


    if complaint is None:

        return "Complaint not found"


    return render_template(
        "track_result.html",
        complaint=complaint
    )


# =========================================================
# MY COMPLAINTS
# =========================================================

@app.route("/my-complaints")
def my_complaints():

    if session.get("role") != "user":

        return redirect(url_for("login"))


    connection = get_db_connection()


    complaints = connection.execute(
        """
        SELECT *
        FROM complaints
        WHERE citizen_name = ?
        ORDER BY id DESC
        """,
        (session["name"],)
    ).fetchall()


    connection.close()


    return render_template(
        "my_complaints.html",
        complaints=complaints
    )


# =========================================================
# ADMIN UPDATE COMPLAINT
# =========================================================

@app.route(
    "/admin/update-complaint/<int:complaint_id>",
    methods=["POST"]
)
def update_complaint(complaint_id):

    if session.get("role") != "admin":

        return redirect(url_for("login"))


    department = request.form["department"]

    status = request.form["status"]


    connection = get_db_connection()


    connection.execute(
        """
        UPDATE complaints
        SET department = ?,
            status = ?
        WHERE id = ?
        """,
        (
            department,
            status,
            complaint_id
        )
    )


    connection.commit()

    connection.close()


    return redirect(
        url_for("admin_dashboard")
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    app.run(debug=True)
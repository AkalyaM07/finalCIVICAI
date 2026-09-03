from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime, timedelta
import uuid
import os

from ai.ai_engine import analyze_complaint


app = Flask(__name__)

app.secret_key = "civicai_secret_key"

DATABASE = "civicai.db"

UPLOAD_FOLDER = "static/uploads"
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

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
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

        if user:

            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["email"] = user["email"]
            session["role"] = user["role"]

            if role == "admin":
                return redirect(url_for("admin_dashboard"))

            return redirect(url_for("user_dashboard"))

        return render_template(
            "login.html",
            error="Invalid email, password or role"
        )

    return render_template("login.html")


# =========================================================
# SIGNUP
# =========================================================

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        connection = get_db_connection()

        try:

            connection.execute(
                """
                INSERT INTO users
                (name, email, password, role)
                VALUES (?, ?, ?, ?)
                """,
                (name, email, password, role)
            )

            connection.commit()

        except sqlite3.IntegrityError:

            connection.close()

            return render_template(
                "signup.html",
                error="Email already exists"
            )

        connection.close()

        return redirect(url_for("login"))

    return render_template("signup.html")


# =========================================================
# CITIZEN DASHBOARD
# =========================================================

@app.route("/user-dashboard")
def user_dashboard():

    if "user_id" not in session:
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

    if "user_id" not in session or session.get("role") != "admin":
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

    # Convert database rows into dictionaries
    # and calculate SLA status
    complaint_list = []

    now = datetime.now()

    for complaint in complaints:

        complaint = dict(complaint)

        sla_status = "No SLA"

        if complaint.get("sla_deadline"):

            try:

                deadline = datetime.fromisoformat(
                    complaint["sla_deadline"]
                )

                # Resolved complaints should not be marked overdue
                if complaint["status"] == "Resolved":

                    sla_status = "Resolved"

                elif now > deadline:

                    sla_status = "Overdue"

                else:

                    sla_status = "Within SLA"

            except ValueError:

                sla_status = "No SLA"

        complaint["sla_status"] = sla_status

        complaint_list.append(complaint)

    # =====================================================
    # DASHBOARD STATISTICS
    # =====================================================

    total_complaints = len(complaint_list)

    submitted_count = sum(
        1 for c in complaint_list
        if c["status"] == "Submitted"
    )

    in_progress_count = sum(
        1 for c in complaint_list
        if c["status"] == "In Progress"
    )

    resolved_count = sum(
        1 for c in complaint_list
        if c["status"] == "Resolved"
    )

    overdue_count = sum(
        1 for c in complaint_list
        if c["sla_status"] == "Overdue"
    )

    within_sla_count = sum(
        1 for c in complaint_list
        if c["sla_status"] == "Within SLA"
    )

    return render_template(
        "admin_dashboard.html",
        complaints=complaint_list,
        total_complaints=total_complaints,
        submitted_count=submitted_count,
        in_progress_count=in_progress_count,
        resolved_count=resolved_count,
        overdue_count=overdue_count,
        within_sla_count=within_sla_count
    )


# =========================================================
# TEXT COMPLAINT REPORT PAGE
# =========================================================

@app.route("/report")
def report():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("report.html")


# =========================================================
# SUBMIT TEXT COMPLAINT
# =========================================================

@app.route("/submit-complaint", methods=["POST"])
def submit_complaint():

    if "user_id" not in session:
        return redirect(url_for("login"))

    phone = request.form.get("phone", "")
    description = request.form.get("description", "")
    location = request.form.get("location", "")

    # =====================================================
    # GENERATE COMPLAINT ID
    # =====================================================

    complaint_id = "CIV-" + str(uuid.uuid4())[:8].upper()

    # =====================================================
    # AI TEXT ANALYSIS
    # =====================================================

    ai_result = analyze_complaint(description)

    category = ai_result["category"]
    priority = ai_result["priority"]
    department = ai_result["department"]
    confidence = ai_result["confidence"]
    sla_hours = ai_result["sla_hours"]

    # =====================================================
    # TIME + SLA DEADLINE
    # =====================================================

    created_at = datetime.now()

    sla_deadline = created_at + timedelta(
        hours=sla_hours
    )

    # =====================================================
    # STATUS
    # =====================================================

    status = "Submitted"

    # =====================================================
    # IMAGE
    # =====================================================

    image_path = None

    image = request.files.get("image")

    if image and image.filename:

        filename = (
            str(uuid.uuid4())
            + "_"
            + image.filename
        )

        image_path = os.path.join(
            UPLOAD_FOLDER,
            filename
        )

        image.save(image_path)

    # =====================================================
    # SAVE TO DATABASE
    # =====================================================

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
            phone,
            description,
            category,
            priority,
            department,
            location,
            status,
            "Text",
            created_at.isoformat(),
            sla_deadline.isoformat(),
            confidence,
            image_path
        )
    )

    connection.commit()
    connection.close()

    # =====================================================
    # SUCCESS PAGE
    # =====================================================

    return render_template(
        "success.html",
        complaint_id=complaint_id,
        category=category,
        priority=priority,
        department=department,
        confidence=confidence,
        sla_hours=sla_hours,
        status=status
    )


# =========================================================
# IMAGE REPORT PAGE
# =========================================================

@app.route("/image-report")
def image_report():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("image_report.html")


# =========================================================
# SUBMIT IMAGE COMPLAINT
# =========================================================

@app.route("/submit-image-complaint", methods=["POST"])
def submit_image_complaint():

    if "user_id" not in session:
        return redirect(url_for("login"))

    image = request.files.get("image")

    if not image or not image.filename:

        return redirect(
            url_for("image_report")
        )

    complaint_id = "CIV-" + str(uuid.uuid4())[:8].upper()

    filename = (
        str(uuid.uuid4())
        + "_"
        + image.filename
    )

    image_path = os.path.join(
        UPLOAD_FOLDER,
        filename
    )

    image.save(image_path)

    # Image ML is still being integrated
    category = "Pending Image AI Analysis"
    priority = "Pending"
    department = "Pending"

    created_at = datetime.now()

    # Temporary SLA until Image ML gives category
    sla_hours = 48

    sla_deadline = created_at + timedelta(
        hours=sla_hours
    )

    status = "Submitted"

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
            "Image based complaint",
            category,
            priority,
            department,
            "",
            status,
            "Image",
            created_at.isoformat(),
            sla_deadline.isoformat(),
            0.0,
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
        confidence=0.0,
        sla_hours=sla_hours,
        status=status
    )


# =========================================================
# TRACK COMPLAINT PAGE
# =========================================================

@app.route("/track")
def track():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("track.html")


# =========================================================
# TRACK COMPLAINT
# =========================================================

@app.route("/track-complaint", methods=["POST"])
def track_complaint():

    if "user_id" not in session:
        return redirect(url_for("login"))

    complaint_id = request.form.get(
        "complaint_id",
        ""
    ).strip()

    citizen_name = session["name"]

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
            citizen_name
        )
    ).fetchone()

    connection.close()

    if not complaint:

        return render_template(
            "track_result.html",
            complaint=None,
            error="Complaint not found"
        )

    complaint = dict(complaint)

    # =====================================================
    # CALCULATE SLA STATUS
    # =====================================================

    sla_status = "No SLA"

    if complaint.get("sla_deadline"):

        try:

            deadline = datetime.fromisoformat(
                complaint["sla_deadline"]
            )

            if complaint["status"] == "Resolved":

                sla_status = "Resolved"

            elif datetime.now() > deadline:

                sla_status = "Overdue"

            else:

                sla_status = "Within SLA"

        except ValueError:

            sla_status = "No SLA"

    complaint["sla_status"] = sla_status

    return render_template(
        "track_result.html",
        complaint=complaint,
        error=None
    )


# =========================================================
# MY COMPLAINTS
# =========================================================

@app.route("/my-complaints")
def my_complaints():

    if "user_id" not in session:
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

    complaint_list = []

    now = datetime.now()

    for complaint in complaints:

        complaint = dict(complaint)

        sla_status = "No SLA"

        if complaint.get("sla_deadline"):

            try:

                deadline = datetime.fromisoformat(
                    complaint["sla_deadline"]
                )

                if complaint["status"] == "Resolved":

                    sla_status = "Resolved"

                elif now > deadline:

                    sla_status = "Overdue"

                else:

                    sla_status = "Within SLA"

            except ValueError:

                sla_status = "No SLA"

        complaint["sla_status"] = sla_status

        complaint_list.append(complaint)

    return render_template(
        "my_complaints.html",
        complaints=complaint_list
    )


# =========================================================
# ADMIN UPDATE COMPLAINT
# =========================================================

@app.route(
    "/admin/update-complaint/<int:complaint_id>",
    methods=["POST"]
)
def update_complaint(complaint_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "admin":
        return redirect(url_for("login"))

    department = request.form.get(
        "department",
        ""
    )

    status = request.form.get(
        "status",
        ""
    )

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
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )
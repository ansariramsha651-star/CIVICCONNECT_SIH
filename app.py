from flask import Flask, render_template, request, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

from classifier import classify_complaint
from duplicate_detector import find_duplicate


app = Flask(__name__)

# -----------------------------
# APP CONFIGURATION
# -----------------------------

app.secret_key = "civicconnect-secret-key"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///complaints.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# -----------------------------
# USER MODEL
# -----------------------------

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(200),
        nullable=False
    )

    role = db.Column(
        db.String(20),
        default="citizen"
    )


# -----------------------------
# COMPLAINT MODEL
# -----------------------------

class Complaint(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        nullable=False
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=False
    )

    location = db.Column(
        db.String(200),
        nullable=False
    )

    category = db.Column(
        db.String(100),
        nullable=True
    )

    department = db.Column(
        db.String(100),
        nullable=True
    )

    priority = db.Column(
        db.String(50),
        nullable=True
    )

    status = db.Column(
        db.String(50),
        default="Pending"
    )

    duplicate_of = db.Column(
        db.Integer,
        nullable=True
    )

    duplicate_similarity = db.Column(
        db.Float,
        nullable=True
    )

    user = db.relationship(
        "User",
        backref="complaints"
    )


# -----------------------------
# CREATE DATABASE
# -----------------------------

with app.app_context():
    db.create_all()


# -----------------------------
# HOME
# -----------------------------

@app.route("/")
def home():

    return render_template("index.html")


# -----------------------------
# SIGNUP
# -----------------------------

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:
            return "Email already registered!"

        hashed_password = generate_password_hash(
            password
        )

        new_user = User(
            name=name,
            email=email,
            password=hashed_password,
            role="citizen"
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("signup.html")


# -----------------------------
# LOGIN
# -----------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(
            email=email
        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):

            session["user_id"] = user.id
            session["user_name"] = user.name
            session["user_role"] = user.role

            if user.role == "authority":

                return redirect(
                    url_for("admin_dashboard")
                )

            return redirect(
                url_for("dashboard")
            )

        return "Invalid email or password!"

    return render_template("login.html")


# -----------------------------
# LOGOUT
# -----------------------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# -----------------------------
# CITIZEN DASHBOARD
# -----------------------------

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    user = User.query.get(
        session["user_id"]
    )

    if user is None:

        session.clear()

        return redirect(
            url_for("login")
        )

    user_complaints = Complaint.query.filter_by(
        user_id=user.id
    ).all()

    total_complaints = len(
        user_complaints
    )

    pending_complaints = Complaint.query.filter_by(
        user_id=user.id,
        status="Pending"
    ).count()

    resolved_complaints = Complaint.query.filter_by(
        user_id=user.id,
        status="Resolved"
    ).count()

    return render_template(
        "dashboard.html",
        user=user,
        complaints=user_complaints,
        total_complaints=total_complaints,
        pending_complaints=pending_complaints,
        resolved_complaints=resolved_complaints
    )


# -----------------------------
# MY COMPLAINTS
# -----------------------------

@app.route("/complaints")
def complaints():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    user_id = session["user_id"]

    user_complaints = Complaint.query.filter_by(
        user_id=user_id
    ).all()

    return render_template(
        "complaints.html",
        complaints=user_complaints
    )


# -----------------------------
# SUBMIT COMPLAINT
# -----------------------------

@app.route("/submit", methods=["GET", "POST"])
def submit_complaint():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        title = request.form["title"]
        description = request.form["description"]
        location = request.form["location"]

        user_id = session["user_id"]

        # -------------------------
        # AI CLASSIFICATION
        # -------------------------

        category, department, priority = classify_complaint(
            description
        )

        # -------------------------
        # DUPLICATE DETECTION
        # -------------------------

        existing_complaints = Complaint.query.all()

        duplicate, similarity = find_duplicate(
            description,
            existing_complaints
        )

        # -------------------------
        # CREATE COMPLAINT
        # -------------------------

        new_complaint = Complaint(

            user_id=user_id,

            name=name,

            email=email,

            title=title,

            description=description,

            location=location,

            category=category,

            department=department,

            priority=priority,

            duplicate_of=(
                duplicate.id
                if duplicate
                else None
            ),

            duplicate_similarity=similarity
        )

        db.session.add(
            new_complaint
        )

        db.session.commit()

        return redirect(
            url_for("dashboard")
        )

    return render_template(
        "submit.html"
    )


# -----------------------------
# AUTHORITY DASHBOARD
# -----------------------------

@app.route("/admin/dashboard")
def admin_dashboard():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    if session.get("user_role") != "authority":

        return "Access denied!"

    all_complaints = Complaint.query.all()

    total_complaints = Complaint.query.count()

    pending_complaints = Complaint.query.filter_by(
        status="Pending"
    ).count()

    resolved_complaints = Complaint.query.filter_by(
        status="Resolved"
    ).count()

    high_priority = Complaint.query.filter_by(
        priority="High"
    ).count()

    return render_template(
        "admin_dashboard.html",

        complaints=all_complaints,

        total_complaints=total_complaints,

        pending_complaints=pending_complaints,

        resolved_complaints=resolved_complaints,

        high_priority=high_priority
    )


# -----------------------------
# UPDATE COMPLAINT STATUS
# -----------------------------

@app.route(
    "/admin/update-status/<int:complaint_id>",
    methods=["POST"]
)
def update_status(complaint_id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    if session.get("user_role") != "authority":

        return "Access denied!"

    complaint = Complaint.query.get_or_404(
        complaint_id
    )

    new_status = request.form["status"]

    complaint.status = new_status

    db.session.commit()

    return redirect(
        url_for("admin_dashboard")
    )


# -----------------------------
# TEMPORARY AUTHORITY TESTING
# -----------------------------

@app.route("/make-authority")
def make_authority():

    user = User.query.first()

    if user:

        user.role = "authority"

        db.session.commit()

        return f"{user.name} is now an authority!"

    return "No user found!"


# -----------------------------
# RUN APPLICATION
# -----------------------------

if __name__ == "__main__":

    app.run(
        debug=True
    )
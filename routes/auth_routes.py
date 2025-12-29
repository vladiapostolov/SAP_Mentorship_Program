from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from services.auth_service import authenticate, register_user, get_user_by_email

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/")
def home():
    return render_template("welcome.html")

@auth_bp.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        user = authenticate(email, password)
        if user:
            login_user(user)
            return redirect(url_for("dashboard.dashboard"))
        flash("Invalid email or password", "danger")
    return render_template("login.html")

@auth_bp.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        first_name = request.form["first_name"].strip()
        last_name = request.form["last_name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if get_user_by_email(email):
            flash("Email already registered", "warning")
            return render_template("register.html")

        register_user(first_name, last_name, email, password, role="STAFF")
        flash("Account created. Please login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))

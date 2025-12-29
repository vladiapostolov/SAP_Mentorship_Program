from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from services.inventory_service import dashboard_stats
from db.connection import db_cursor
from werkzeug.security import generate_password_hash

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    stats = dashboard_stats()
    if current_user.role == 'ADMIN':
        with db_cursor() as (_, cur):
            cur.execute("SELECT COUNT(*) as total_users FROM users")
            user_count = cur.fetchone()
            stats = stats or {}
            stats['total_users'] = user_count['total_users'] if user_count else 0
    return render_template("dashboard.html", stats=stats, user=current_user)

@dashboard_bp.route("/users")
@login_required
def manage_users():
    if current_user.role != 'ADMIN':
        flash("Access denied. Admin privileges required.", "danger")
        return redirect(url_for('dashboard.dashboard'))
    
    with db_cursor() as (_, cur):
        cur.execute("SELECT id, first_name, last_name, email, role, is_active, created_at FROM users ORDER BY created_at DESC")
        users = cur.fetchall()
    
    return render_template("users.html", users=users)

@dashboard_bp.route("/users/add", methods=["POST"])
@login_required
def add_user():
    if current_user.role != 'ADMIN':
        flash("Access denied. Admin privileges required.", "danger")
        return redirect(url_for('dashboard.dashboard'))
    
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role', 'STAFF')
    
    if not all([first_name, last_name, email, password]):
        flash("All fields are required.", "danger")
        return redirect(url_for('dashboard.manage_users'))
    
    pwd_hash = generate_password_hash(password)
    
    try:
        with db_cursor() as (conn, cur):
            cur.execute("""
                INSERT INTO users (first_name, last_name, email, password_hash, role)
                VALUES (%s, %s, %s, %s, %s)
            """, (first_name, last_name, email, pwd_hash, role))
            conn.commit()
        flash("User added successfully.", "success")
    except Exception as e:
        flash(f"Error adding user: {str(e)}", "danger")
    
    return redirect(url_for('dashboard.manage_users'))

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from services.statistics_service import (
    get_quantity_changes,
    get_top_added_items,
    get_top_removed_items,
    get_activity_by_day,
    get_activity_by_type,
    get_statistics_summary
)
from db.connection import db_cursor

reports_bp = Blueprint("reports", __name__)

@reports_bp.route("/reports")
@login_required
def reports():
    # Only admins can view reports
    if current_user.role != 'ADMIN':
        flash("Access denied. Admin privileges required.", "danger")
        return redirect(url_for('dashboard.dashboard'))
    
    # Get time period from query params (default 30 days)
    days = int(request.args.get('days', 30))
    if days not in [7, 30, 90]:
        days = 30
    
    # Get all statistics data
    summary = get_statistics_summary(days=days)
    daily_activity = get_activity_by_day(days=days)
    type_activity = get_activity_by_type(days=days)
    top_added = get_top_added_items(days=days, limit=5)
    top_removed = get_top_removed_items(days=days, limit=5)
    
    # Get low stock items
    with db_cursor() as (_, cur):
        cur.execute("""
            SELECT name, type, quantity, min_quantity
            FROM items
            WHERE quantity < min_quantity AND quantity > 0
            ORDER BY (quantity / min_quantity) ASC
            LIMIT 10
        """)
        low_stock = cur.fetchall()
    
    return render_template(
        "reports.html",
        days=days,
        summary=summary,
        daily_activity=daily_activity,
        type_activity=type_activity,
        top_added=top_added,
        top_removed=top_removed,
        low_stock=low_stock
    )

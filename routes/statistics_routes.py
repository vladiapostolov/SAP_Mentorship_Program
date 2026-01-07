from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from services.statistics_service import (
    get_quantity_changes,
    get_top_added_items,
    get_top_removed_items,
    get_activity_by_day,
    get_activity_by_type,
    get_statistics_summary
)

statistics_bp = Blueprint("statistics", __name__)

@statistics_bp.route("/statistics")
@login_required
def statistics():
    # Only admins can view statistics
    if current_user.role != 'ADMIN':
        flash("Access denied. Admin privileges required.", "danger")
        return redirect(url_for('dashboard.dashboard'))
    
    # Get time period from query params (default 30 days)
    days = int(request.args.get('days', 30))
    if days not in [7, 30, 90]:
        days = 30
    
    # Get all statistics data
    summary = get_statistics_summary(days=days)
    quantity_changes = get_quantity_changes(days=days)
    top_added = get_top_added_items(days=days, limit=10)
    top_removed = get_top_removed_items(days=days, limit=10)
    daily_activity = get_activity_by_day(days=days)
    type_activity = get_activity_by_type(days=days)
    
    return render_template(
        "statistics.html",
        days=days,
        summary=summary,
        quantity_changes=quantity_changes,
        top_added=top_added,
        top_removed=top_removed,
        daily_activity=daily_activity,
        type_activity=type_activity
    )

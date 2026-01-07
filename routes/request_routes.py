from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from services.request_service import (
    create_request,
    get_admin_requests,
    get_user_requests,
    update_request_status,
    get_pending_requests_count
)
from services.inventory_service import list_inventory

request_bp = Blueprint("requests", __name__)

@request_bp.route("/requests")
@login_required
def requests_list():
    """Show requests - admin sees all, staff sees their own"""
    if current_user.role == 'ADMIN':
        # Admin view - show all requests with filtering
        status_filter = request.args.get('status', 'PENDING')
        if status_filter == 'ALL':
            requests = get_admin_requests()
        else:
            requests = get_admin_requests(status=status_filter)
        return render_template("admin_requests.html", requests=requests, status_filter=status_filter)
    else:
        # Staff view - show their own requests
        user_requests = get_user_requests(current_user.id)
        return render_template("staff_requests.html", requests=user_requests)

@request_bp.route("/requests/create", methods=["GET", "POST"])
@login_required
def create_request_page():
    """Staff creates a new request"""
    if current_user.role == 'ADMIN':
        flash("Admins don't need to create requests.", "info")
        return redirect(url_for("requests.requests_list"))
    
    if request.method == "POST":
        item_id = int(request.form["item_id"])
        quantity = int(request.form["quantity"])
        message = request.form.get("message", "").strip() or None
        
        try:
            create_request(current_user.id, item_id, quantity, message)
            flash("Request sent to admin successfully!", "success")
            return redirect(url_for("requests.requests_list"))
        except Exception as e:
            flash(f"Error creating request: {e}", "danger")
    
    # Get all items for the form
    items = list_inventory()
    return render_template("create_request.html", items=items)

@request_bp.route("/requests/<int:request_id>/update", methods=["POST"])
@login_required
def update_request(request_id):
    """Admin updates request status"""
    if current_user.role != 'ADMIN':
        flash("Access denied. Admin privileges required.", "danger")
        return redirect(url_for("requests.requests_list"))
    
    status = request.form.get("status")
    admin_note = request.form.get("admin_note", "").strip() or None
    
    if status not in ["APPROVED", "REJECTED", "COMPLETED"]:
        flash("Invalid status.", "danger")
        return redirect(url_for("requests.requests_list"))
    
    try:
        update_request_status(request_id, status, admin_note)
        flash(f"Request {status.lower()} successfully!", "success")
    except Exception as e:
        flash(f"Error updating request: {e}", "danger")
    
    return redirect(url_for("requests.requests_list"))

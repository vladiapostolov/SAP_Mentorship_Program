from db.connection import db_cursor
from datetime import datetime

def create_request(user_id, item_id, quantity, message=None):
    """Create a new request from staff to admin"""
    with db_cursor() as (conn, cur):
        cur.execute("""
            INSERT INTO requests (user_id, item_id, quantity, message, status)
            VALUES (%s, %s, %s, %s, 'PENDING')
        """, (user_id, item_id, quantity, message))
        conn.commit()
        return cur.lastrowid

def get_admin_requests(status=None, limit=50):
    """Get all requests for admin review"""
    with db_cursor() as (_, cur):
        if status:
            cur.execute("""
                SELECT 
                    r.id,
                    r.user_id,
                    r.item_id,
                    r.quantity,
                    r.message,
                    r.status,
                    r.created_at,
                    r.updated_at,
                    CONCAT(u.first_name, ' ', u.last_name) as user_name,
                    u.email as user_email,
                    i.name as item_name,
                    i.type as item_type,
                    i.qr_code as item_qr
                FROM requests r
                JOIN users u ON r.user_id = u.id
                JOIN items i ON r.item_id = i.id
                WHERE r.status = %s
                ORDER BY r.created_at DESC
                LIMIT %s
            """, (status, limit))
        else:
            cur.execute("""
                SELECT 
                    r.id,
                    r.user_id,
                    r.item_id,
                    r.quantity,
                    r.message,
                    r.status,
                    r.created_at,
                    r.updated_at,
                    CONCAT(u.first_name, ' ', u.last_name) as user_name,
                    u.email as user_email,
                    i.name as item_name,
                    i.type as item_type,
                    i.qr_code as item_qr
                FROM requests r
                JOIN users u ON r.user_id = u.id
                JOIN items i ON r.item_id = i.id
                ORDER BY r.created_at DESC
                LIMIT %s
            """, (limit,))
        return cur.fetchall()

def get_user_requests(user_id, limit=20):
    """Get requests for a specific user"""
    with db_cursor() as (_, cur):
        cur.execute("""
            SELECT 
                r.id,
                r.item_id,
                r.quantity,
                r.message,
                r.status,
                r.created_at,
                r.updated_at,
                i.name as item_name,
                i.type as item_type
            FROM requests r
            JOIN items i ON r.item_id = i.id
            WHERE r.user_id = %s
            ORDER BY r.created_at DESC
            LIMIT %s
        """, (user_id, limit))
        return cur.fetchall()

def update_request_status(request_id, status, admin_note=None):
    """Update request status (APPROVED, REJECTED, COMPLETED)"""
    with db_cursor() as (conn, cur):
        cur.execute("""
            UPDATE requests 
            SET status = %s, admin_note = %s, updated_at = NOW()
            WHERE id = %s
        """, (status, admin_note, request_id))
        conn.commit()

def get_pending_requests_count():
    """Get count of pending requests"""
    with db_cursor() as (_, cur):
        cur.execute("SELECT COUNT(*) as count FROM requests WHERE status = 'PENDING'")
        result = cur.fetchone()
        return result['count'] if result else 0

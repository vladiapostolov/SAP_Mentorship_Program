from db.connection import db_cursor
from config import Config

ALLOWED_TYPES = {
    "BATTERY","FIN","CONTROLLER","MOTOR","ESC","FRAME","PROPELLER","CAMERA","DRONE","OTHER"
}

def dashboard_stats(warehouse_id: int = None):
    warehouse_id = warehouse_id or Config.DEFAULT_WAREHOUSE_ID
    with db_cursor() as (_, cur):
        cur.execute("SELECT * FROM vw_dashboard_warehouse WHERE warehouse_id=%s", (warehouse_id,))
        return cur.fetchone()

def list_inventory(warehouse_id: int = None):
    warehouse_id = warehouse_id or Config.DEFAULT_WAREHOUSE_ID
    with db_cursor() as (_, cur):
        cur.execute("""
            SELECT * FROM vw_inventory
            WHERE warehouse_id=%s AND quantity > 0
            ORDER BY name
        """, (warehouse_id,))
        return cur.fetchall()

def get_item_details_by_qr(qr_code: str):
    with db_cursor() as (_, cur):
        cur.execute("SELECT * FROM vw_item_details WHERE qr_code=%s", (qr_code,))
        return cur.fetchone()

def get_item_events(item_id: int, limit: int = 20):
    with db_cursor() as (_, cur):
        cur.execute("""
            SELECT * FROM vw_item_events
            WHERE item_id=%s
            ORDER BY timestamp_created DESC
            LIMIT %s
        """, (item_id, limit))
        return cur.fetchall()

def add_item(name, description, type_, quantity, qr_code, warehouse_id=None):
    warehouse_id = warehouse_id or Config.DEFAULT_WAREHOUSE_ID
    if type_ not in ALLOWED_TYPES:
        raise ValueError("Invalid type")
    
    # Generate unique SKU
    import uuid
    sku = f"ITEM{uuid.uuid4().hex[:8].upper()}"
    
    with db_cursor() as (conn, cur):
        cur.execute("""
            INSERT INTO items (sku, warehouse_id, name, description, type, quantity, qr_code)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (sku, warehouse_id, name, description, type_, int(quantity), qr_code))
        conn.commit()

def apply_stock_action(item_id: int, user_id: int, action: str, qty: int, note: str = None):
    """
    action: ADD / REMOVE / RETURN
    qty must be positive
    updates items.quantity and inserts warehouse_events in one transaction
    """
    if qty <= 0:
        raise ValueError("Quantity must be > 0")
    if action not in ("ADD", "REMOVE", "RETURN"):
        raise ValueError("Invalid action")

    delta = qty if action in ("ADD", "RETURN") else -qty

    with db_cursor() as (_, cur):
        # lock item row to avoid race conditions
        cur.execute("SELECT id, warehouse_id, quantity FROM items WHERE id=%s FOR UPDATE", (item_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError("Item not found")

        new_qty = row["quantity"] + delta
        if new_qty < 0:
            raise ValueError("Not enough stock to remove")

        cur.execute("UPDATE items SET quantity=%s WHERE id=%s", (new_qty, item_id))

        cur.execute("""
            INSERT INTO warehouse_events (warehouse_id, item_id, user_id, action, quantity, note)
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (row["warehouse_id"], item_id, user_id, action, qty, note))

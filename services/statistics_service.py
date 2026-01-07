from db.connection import db_cursor
from config import Config
from datetime import datetime, timedelta

def get_quantity_changes(warehouse_id=None, days=30):
    """Get items with quantity changes in the last N days"""
    warehouse_id = warehouse_id or Config.DEFAULT_WAREHOUSE_ID
    
    with db_cursor() as (_, cur):
        cur.execute("""
            SELECT 
                i.id,
                i.name,
                i.type,
                i.sku,
                i.quantity as current_quantity,
                COALESCE(SUM(CASE WHEN we.action = 'ADD' THEN we.quantity ELSE 0 END), 0) as total_added,
                COALESCE(SUM(CASE WHEN we.action = 'REMOVE' THEN we.quantity ELSE 0 END), 0) as total_removed,
                COUNT(we.id) as total_events
            FROM items i
            LEFT JOIN warehouse_events we ON i.id = we.item_id 
                AND we.timestamp_created >= DATE_SUB(NOW(), INTERVAL %s DAY)
            WHERE i.warehouse_id = %s
            GROUP BY i.id, i.name, i.type, i.sku, i.quantity
            HAVING total_events > 0
            ORDER BY total_events DESC, i.name
        """, (days, warehouse_id))
        return cur.fetchall()

def get_top_added_items(warehouse_id=None, days=30, limit=10):
    """Get items with most quantity added"""
    warehouse_id = warehouse_id or Config.DEFAULT_WAREHOUSE_ID
    
    with db_cursor() as (_, cur):
        cur.execute("""
            SELECT 
                i.name,
                i.type,
                i.sku,
                SUM(we.quantity) as total_added,
                COUNT(we.id) as add_count
            FROM items i
            JOIN warehouse_events we ON i.id = we.item_id
            WHERE we.action = 'ADD'
                AND i.warehouse_id = %s
                AND we.timestamp_created >= DATE_SUB(NOW(), INTERVAL %s DAY)
            GROUP BY i.id, i.name, i.type, i.sku
            ORDER BY total_added DESC
            LIMIT %s
        """, (warehouse_id, days, limit))
        return cur.fetchall()

def get_top_removed_items(warehouse_id=None, days=30, limit=10):
    """Get items with most quantity removed"""
    warehouse_id = warehouse_id or Config.DEFAULT_WAREHOUSE_ID
    
    with db_cursor() as (_, cur):
        cur.execute("""
            SELECT 
                i.name,
                i.type,
                i.sku,
                SUM(we.quantity) as total_removed,
                COUNT(we.id) as remove_count
            FROM items i
            JOIN warehouse_events we ON i.id = we.item_id
            WHERE we.action = 'REMOVE'
                AND i.warehouse_id = %s
                AND we.timestamp_created >= DATE_SUB(NOW(), INTERVAL %s DAY)
            GROUP BY i.id, i.name, i.type, i.sku
            ORDER BY total_removed DESC
            LIMIT %s
        """, (warehouse_id, days, limit))
        return cur.fetchall()

def get_activity_by_day(warehouse_id=None, days=30):
    """Get daily activity summary"""
    warehouse_id = warehouse_id or Config.DEFAULT_WAREHOUSE_ID
    
    with db_cursor() as (_, cur):
        cur.execute("""
            SELECT 
                DATE(timestamp_created) as date,
                SUM(CASE WHEN action = 'ADD' THEN quantity ELSE 0 END) as added,
                SUM(CASE WHEN action = 'REMOVE' THEN quantity ELSE 0 END) as removed,
                COUNT(*) as total_transactions
            FROM warehouse_events
            WHERE warehouse_id = %s
                AND timestamp_created >= DATE_SUB(NOW(), INTERVAL %s DAY)
            GROUP BY DATE(timestamp_created)
            ORDER BY date DESC
        """, (warehouse_id, days))
        return cur.fetchall()

def get_activity_by_type(warehouse_id=None, days=30):
    """Get activity summary by item type"""
    warehouse_id = warehouse_id or Config.DEFAULT_WAREHOUSE_ID
    
    with db_cursor() as (_, cur):
        cur.execute("""
            SELECT 
                i.type,
                COUNT(DISTINCT i.id) as item_count,
                COALESCE(SUM(CASE WHEN we.action = 'ADD' THEN we.quantity ELSE 0 END), 0) as total_added,
                COALESCE(SUM(CASE WHEN we.action = 'REMOVE' THEN we.quantity ELSE 0 END), 0) as total_removed,
                COALESCE(COUNT(we.id), 0) as total_events
            FROM items i
            LEFT JOIN warehouse_events we ON i.id = we.item_id 
                AND we.timestamp_created >= DATE_SUB(NOW(), INTERVAL %s DAY)
            WHERE i.warehouse_id = %s
            GROUP BY i.type
            ORDER BY total_events DESC, i.type
        """, (days, warehouse_id))
        return cur.fetchall()

def get_statistics_summary(warehouse_id=None, days=30):
    """Get overall statistics summary"""
    warehouse_id = warehouse_id or Config.DEFAULT_WAREHOUSE_ID
    
    with db_cursor() as (_, cur):
        cur.execute("""
            SELECT 
                (SELECT COUNT(*) FROM items WHERE warehouse_id = %s AND quantity > 0) as active_items,
                COUNT(*) as total_transactions,
                SUM(CASE WHEN action = 'ADD' THEN quantity ELSE 0 END) as total_added,
                SUM(CASE WHEN action = 'REMOVE' THEN quantity ELSE 0 END) as total_removed,
                COUNT(DISTINCT user_id) as active_users,
                COUNT(DISTINCT DATE(timestamp_created)) as active_days
            FROM warehouse_events
            WHERE warehouse_id = %s
                AND timestamp_created >= DATE_SUB(NOW(), INTERVAL %s DAY)
        """, (warehouse_id, warehouse_id, days))
        return cur.fetchone()

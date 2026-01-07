"""
Script to populate sample warehouse events for testing statistics
"""
from db.connection import db_cursor
from datetime import datetime, timedelta
import random

def populate_sample_events():
    """Add sample warehouse events for the last 30 days"""
    
    # Get existing items and users
    with db_cursor() as (_, cur):
        cur.execute("SELECT id, name FROM items LIMIT 6")
        items = cur.fetchall()
        
        cur.execute("SELECT id FROM users WHERE role='ADMIN' LIMIT 1")
        admin_user = cur.fetchone()
        
        if not items or not admin_user:
            print("❌ Need items and users in database first")
            return
        
        user_id = admin_user['id']
        
    # Generate random events over the last 30 days
    actions = ['ADD', 'REMOVE', 'RETURN']
    events = []
    
    for days_ago in range(30, 0, -1):
        # Random number of events per day (0-5)
        num_events = random.randint(0, 5)
        
        for _ in range(num_events):
            item = random.choice(items)
            action = random.choice(actions)
            
            # ADD actions have higher quantities
            if action == 'ADD':
                quantity = random.randint(5, 20)
            elif action == 'REMOVE':
                quantity = random.randint(1, 10)
            else:  # RETURN
                quantity = random.randint(1, 5)
            
            # Create timestamp for this event
            event_date = datetime.now() - timedelta(days=days_ago)
            event_date = event_date.replace(
                hour=random.randint(8, 17),
                minute=random.randint(0, 59),
                second=random.randint(0, 59)
            )
            
            events.append({
                'warehouse_id': 1,
                'item_id': item['id'],
                'user_id': user_id,
                'action': action,
                'quantity': quantity,
                'timestamp': event_date.strftime('%Y-%m-%d %H:%M:%S'),
                'note': f"Sample {action.lower()} event"
            })
    
    # Insert all events
    with db_cursor() as (conn, cur):
        for event in events:
            cur.execute("""
                INSERT INTO warehouse_events 
                (warehouse_id, item_id, user_id, action, quantity, timestamp_created, note)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                event['warehouse_id'],
                event['item_id'],
                event['user_id'],
                event['action'],
                event['quantity'],
                event['timestamp'],
                event['note']
            ))
        conn.commit()
    
    print(f"✅ Added {len(events)} sample warehouse events")
    print(f"   Events span the last 30 days")
    print(f"   Items involved: {len(items)}")
    

if __name__ == "__main__":
    populate_sample_events()

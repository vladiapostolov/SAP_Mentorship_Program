# db/init_db.py
import mysql.connector
from mysql.connector import Error
from config import Config
from werkzeug.security import generate_password_hash


DDL = [
    # Drop tables if exist (for development)
    "SET FOREIGN_KEY_CHECKS = 0;",
    "DROP TABLE IF EXISTS warehouse_events;",
    "DROP TABLE IF EXISTS items;",
    "DROP TABLE IF EXISTS warehouses;",
    "DROP TABLE IF EXISTS users;",
    "SET FOREIGN_KEY_CHECKS = 1;",

    # Users
    """
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        first_name VARCHAR(50) NOT NULL DEFAULT '',
        last_name  VARCHAR(50) NOT NULL DEFAULT '',
        email VARCHAR(120) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        role ENUM('ADMIN','STAFF') NOT NULL DEFAULT 'STAFF',
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB;
    """,

    # Warehouses
    """
    CREATE TABLE IF NOT EXISTS warehouses (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        timestamp_created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB;
    """,

    # Items
    """
    CREATE TABLE IF NOT EXISTS items (
        id INT AUTO_INCREMENT PRIMARY KEY,
        sku VARCHAR(100) NOT NULL UNIQUE,
        name VARCHAR(120) NOT NULL,
        type VARCHAR(50) NOT NULL,              -- e.g. BATTERY, MOTOR, ESC, FRAME, CONTROLLER, DRONE
        description TEXT NULL,
        quantity INT NOT NULL DEFAULT 0,
        min_quantity INT NOT NULL DEFAULT 5,
        location VARCHAR(50) NULL,              -- e.g. "Shelf B3"
        warehouse_id INT NOT NULL DEFAULT 1,
        qr_code VARCHAR(255) NULL,
        timestamp_created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_items_type (type),
        INDEX idx_items_quantity (quantity),
        INDEX idx_items_warehouse (warehouse_id)
    ) ENGINE=InnoDB;
    """,

    # Warehouse events (audit log)
    """
    CREATE TABLE IF NOT EXISTS warehouse_events (
        id INT AUTO_INCREMENT PRIMARY KEY,
        warehouse_id INT NOT NULL,
        item_id INT NOT NULL,
        user_id INT NOT NULL,
        action ENUM('ADD','REMOVE','RETURN') NOT NULL,
        quantity INT NOT NULL,
        note VARCHAR(255) NULL,
        timestamp_created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

        CONSTRAINT fk_we_warehouse FOREIGN KEY (warehouse_id)
            REFERENCES warehouses(id)
            ON DELETE RESTRICT ON UPDATE CASCADE,

        CONSTRAINT fk_we_item FOREIGN KEY (item_id)
            REFERENCES items(id)
            ON DELETE RESTRICT ON UPDATE CASCADE,

        CONSTRAINT fk_we_user FOREIGN KEY (user_id)
            REFERENCES users(id)
            ON DELETE RESTRICT ON UPDATE CASCADE,

        INDEX idx_we_warehouse_ts (warehouse_id, timestamp_created),
        INDEX idx_we_item_ts (item_id, timestamp_created),
        INDEX idx_we_user_ts (user_id, timestamp_created)
    ) ENGINE=InnoDB;
    """,

    # Requests table
    """
    CREATE TABLE IF NOT EXISTS requests (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        item_id INT NOT NULL,
        quantity INT NOT NULL,
        message TEXT NULL,
        status ENUM('PENDING','APPROVED','REJECTED','COMPLETED') NOT NULL DEFAULT 'PENDING',
        admin_note TEXT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

        CONSTRAINT fk_req_user FOREIGN KEY (user_id)
            REFERENCES users(id)
            ON DELETE RESTRICT ON UPDATE CASCADE,

        CONSTRAINT fk_req_item FOREIGN KEY (item_id)
            REFERENCES items(id)
            ON DELETE RESTRICT ON UPDATE CASCADE,

        INDEX idx_req_status (status),
        INDEX idx_req_user (user_id),
        INDEX idx_req_created (created_at)
    ) ENGINE=InnoDB;
    """,

    # Views
    """
    CREATE OR REPLACE VIEW vw_inventory AS
    SELECT 
        i.*,
        CASE WHEN i.quantity < i.min_quantity THEN 1 ELSE 0 END as is_low_stock,
        (SELECT MAX(timestamp_created) FROM warehouse_events WHERE item_id = i.id AND action = 'ADD') as last_in_ts,
        (SELECT MAX(timestamp_created) FROM warehouse_events WHERE item_id = i.id AND action = 'REMOVE') as last_out_ts
    FROM items i;
    """,

    """
    CREATE OR REPLACE VIEW vw_item_details AS
    SELECT 
        i.*,
        (SELECT MAX(timestamp_created) FROM warehouse_events WHERE item_id = i.id AND action = 'ADD') as last_in_ts,
        (SELECT MAX(timestamp_created) FROM warehouse_events WHERE item_id = i.id AND action = 'REMOVE') as last_out_ts,
        (SELECT action FROM warehouse_events WHERE item_id = i.id ORDER BY timestamp_created DESC LIMIT 1) as last_event_action,
        (SELECT quantity FROM warehouse_events WHERE item_id = i.id ORDER BY timestamp_created DESC LIMIT 1) as last_event_qty,
        (SELECT u.first_name FROM warehouse_events we JOIN users u ON we.user_id = u.id WHERE we.item_id = i.id ORDER BY we.timestamp_created DESC LIMIT 1) as last_event_by,
        (SELECT timestamp_created FROM warehouse_events WHERE item_id = i.id ORDER BY timestamp_created DESC LIMIT 1) as last_event_ts
    FROM items i;
    """,

    """
    CREATE OR REPLACE VIEW vw_item_events AS
    SELECT we.*, CONCAT(u.first_name, ' ', u.last_name) as user_name
    FROM warehouse_events we
    JOIN users u ON we.user_id = u.id;
    """,

    """
    CREATE OR REPLACE VIEW vw_dashboard_warehouse AS
    SELECT 
        warehouse_id,
        COUNT(*) as total_items,
        SUM(quantity) as total_quantity,
        SUM(CASE WHEN quantity < min_quantity THEN 1 ELSE 0 END) as low_stock_items,
        (SELECT COUNT(*) FROM warehouse_events WHERE warehouse_id = i.warehouse_id AND DATE(timestamp_created) = CURDATE()) as events_today,
        (SELECT COALESCE(SUM(quantity), 0) FROM warehouse_events WHERE warehouse_id = i.warehouse_id AND action = 'ADD' AND DATE(timestamp_created) = CURDATE()) as inbound_qty_today,
        (SELECT COALESCE(SUM(quantity), 0) FROM warehouse_events WHERE warehouse_id = i.warehouse_id AND action = 'REMOVE' AND DATE(timestamp_created) = CURDATE()) as outbound_qty_today
    FROM items i
    GROUP BY warehouse_id;
    """,
]


def main():
    try:
        # 1) Connect without DB to ensure DB exists
        conn = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
        )
        cur = conn.cursor()
        cur.execute(
            f"CREATE DATABASE IF NOT EXISTS `{Config.DB_NAME}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
        )
        conn.commit()
        cur.close()
        conn.close()

        # 2) Connect to the DB and create tables
        conn = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
        )
        cur = conn.cursor()
        for stmt in DDL:
            cur.execute(stmt)
        conn.commit()
        cur.close()
        conn.close()

        print("✅ MySQL DB initialized (users, items, warehouse_events).")

        # 3) Insert default data
        conn = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
        )
        cur = conn.cursor()

        # Insert default warehouse
        try:
            cur.execute("""
                INSERT INTO warehouses (id, name)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE id=id
            """, (1, "Main Warehouse"))
            conn.commit()
            print("✅ Default warehouse created: Main Warehouse")
        except Error as e:
            print(f"⚠️ Could not create default warehouse: {e}")

        # Insert default admin user
        try:
            cur.execute("""
                INSERT INTO users (first_name, last_name, email, password_hash, role)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE id=id
            """, ("Admin", "User", "admin@dronify.com", generate_password_hash("admin123"), "ADMIN"))
            conn.commit()
            print("✅ Default admin user created: admin@dronify.com / admin123")
        except Error as e:
            print(f"⚠️ Could not create admin user: {e}")

        # Insert dummy items
        try:
            dummy_items = [
                ("DRONE001", "Quadcopter Drone", "DRONE", "Basic quadcopter drone", 5, 2, "Shelf A1", 1, "QR-DRONE001"),
                ("BAT001", "LiPo Battery 3S", "BATTERY", "3S 2200mAh LiPo battery", 10, 5, "Shelf B2", 1, "QR-BAT001"),
                ("MOT001", "Brushless Motor 2205", "MOTOR", "2205 brushless motor", 8, 3, "Shelf C3", 1, "QR-MOT001"),
                ("ESC001", "30A ESC", "ESC", "30A electronic speed controller", 6, 2, "Shelf D4", 1, "QR-ESC001"),
                ("PROP001", "5x4.5 Propeller", "PROPELLER", "5 inch propeller set", 20, 10, "Shelf E5", 1, "QR-PROP001"),
                ("FRAME001", "250mm Frame", "FRAME", "250mm quadcopter frame", 3, 1, "Shelf F6", 1, "QR-FRAME001"),
            ]
            for item in dummy_items:
                cur.execute("""
                    INSERT INTO items (sku, name, type, description, quantity, min_quantity, location, warehouse_id, qr_code)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE sku=sku
                """, item)
            conn.commit()
            print("✅ Dummy items inserted")
        except Error as e:
            print(f"⚠️ Could not insert dummy items: {e}")

        cur.close()
        conn.close()

    except Error as e:
        print("❌ DB init failed:", e)


if __name__ == "__main__":
    main()

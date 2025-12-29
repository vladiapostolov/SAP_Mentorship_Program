# db/init_db.py
import mysql.connector
from mysql.connector import Error
from config import Config
from werkzeug.security import generate_password_hash


DDL = [
    # Drop tables if exist (for development)
    "SET FOREIGN_KEY_CHECKS = 0;",
    "DROP TABLE IF EXISTS stock_movements;",
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

    # Stock movements (audit log)
    """
    CREATE TABLE IF NOT EXISTS stock_movements (
        id INT AUTO_INCREMENT PRIMARY KEY,
        item_id INT NOT NULL,
        user_id INT NOT NULL,
        movement_type ENUM('IN','OUT') NOT NULL,
        quantity INT NOT NULL,
        note VARCHAR(255) NULL,
        ts TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

        CONSTRAINT fk_sm_item FOREIGN KEY (item_id)
            REFERENCES items(id)
            ON DELETE RESTRICT ON UPDATE CASCADE,

        CONSTRAINT fk_sm_user FOREIGN KEY (user_id)
            REFERENCES users(id)
            ON DELETE RESTRICT ON UPDATE CASCADE,

        INDEX idx_sm_item_ts (item_id, ts),
        INDEX idx_sm_item_type_ts (item_id, movement_type, ts),
        INDEX idx_sm_user_ts (user_id, ts)
    ) ENGINE=InnoDB;
    """,

    # Views
    """
    CREATE OR REPLACE VIEW vw_inventory AS
    SELECT * FROM items;
    """,

    """
    CREATE OR REPLACE VIEW vw_item_details AS
    SELECT * FROM items;
    """,

    """
    CREATE OR REPLACE VIEW vw_item_events AS
    SELECT * FROM stock_movements;
    """,

    """
    CREATE OR REPLACE VIEW vw_dashboard_warehouse AS
    SELECT warehouse_id, COUNT(*) as total_items, SUM(quantity) as total_quantity
    FROM items
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

        print("✅ MySQL DB initialized (users, items, stock_movements).")

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

    except Error as e:
        print("❌ DB init failed:", e)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from db.connection import db_cursor
from werkzeug.security import generate_password_hash

def create_admin():
    try:
        with db_cursor() as (conn, cur):
            cur.execute("""
                INSERT INTO users (first_name, last_name, email, password_hash, role)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE id=id
            """, ("Admin", "User", "admin@dronify.com", generate_password_hash("admin123"), "ADMIN"))
            conn.commit()
        print("✅ Admin user created: admin@dronify.com / admin123")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    create_admin()
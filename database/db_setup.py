# secondhand_market/database/db_setup.py

import mysql.connector

DB_NAME = "secondhand_market"

def get_connection():
    """Return a connection to the MySQL database."""
    # Adjust host, user, password to match your environment
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password='Kkhiladi@420',
        database=DB_NAME
    )

def init_db():
    """
    Initializes the database and tables if they do not exist.
    You can call this once at startup.
    """
    # Connect without specifying database first
    con = mysql.connector.connect(
        host='localhost',
        user='root',
        password='Kkhiladi@420'
    )
    cur = con.cursor()
    # Create database if not exists
    cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME};")
    # Switch to using that database
    cur.execute(f"USE {DB_NAME};")

    # Create tables (simplified)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) NOT NULL,
            email VARCHAR(255),
            phone VARCHAR(50),
            password_hash VARCHAR(255)
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS items (
            item_id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            price DECIMAL(10, 2),
            condition_status VARCHAR(50),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(50) DEFAULT 'Available',
            seller_id INT,
            category VARCHAR(100),
            contact_preference VARCHAR(50),
            location VARCHAR(255),
            image_data LONGBLOB,
            FOREIGN KEY (seller_id) REFERENCES users(user_id)
        );
    """)

    # Create default user if none exists
    cur.execute("SELECT COUNT(*) FROM users")
    user_count = cur.fetchone()[0]
    
    if user_count == 0:
        # Insert default user
        cur.execute("""
            INSERT INTO users (username, email, phone)
            VALUES ('default_user', 'default@example.com', '555-123-4567')
        """)
        con.commit()
        print("Created default user with ID 1")

    con.commit()
    cur.close()
    con.close()

# Check if we need to alter existing tables
def check_and_update_schema():
    """
    Checks if the database schema needs updates and applies them if needed.
    This allows for non-destructive schema updates after initial creation.
    """
    con = get_connection()
    cur = con.cursor()
    
    # Check for missing columns in items table
    cur.execute("SHOW COLUMNS FROM items")
    existing_item_columns = [column[0] for column in cur.fetchall()]
    
    # Add any missing columns to items table
    if "category" not in existing_item_columns:
        cur.execute("ALTER TABLE items ADD COLUMN category VARCHAR(100)")
    
    if "contact_preference" not in existing_item_columns:
        cur.execute("ALTER TABLE items ADD COLUMN contact_preference VARCHAR(50)")
    
    if "location" not in existing_item_columns:
        cur.execute("ALTER TABLE items ADD COLUMN location VARCHAR(255)")
    
    if "image_data" not in existing_item_columns:
        cur.execute("ALTER TABLE items ADD COLUMN image_data LONGBLOB")
    
    # Check for missing columns in users table
    cur.execute("SHOW COLUMNS FROM users")
    existing_user_columns = [column[0] for column in cur.fetchall()]
    
    # Add phone column to users table if not exists
    if "phone" not in existing_user_columns:
        cur.execute("ALTER TABLE users ADD COLUMN phone VARCHAR(50)")
        print("Added phone column to users table")
    
    # Ensure default user exists
    cur.execute("SELECT COUNT(*) FROM users")
    user_count = cur.fetchone()[0]
    
    if user_count == 0:
        # Insert default user
        cur.execute("""
            INSERT INTO users (username, email, phone)
            VALUES ('default_user', 'default@example.com', '555-123-4567')
        """)
        con.commit()
        print("Created default user with ID 1")
    
    con.commit()
    cur.close()
    con.close()
    print("Database schema updated successfully!")

# Initialize the database when imported
init_db()
check_and_update_schema()

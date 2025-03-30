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

    # Create categories table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            category_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            parent_category_id INT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_category_id) REFERENCES categories(category_id) ON DELETE SET NULL
        );
    """)

    # Insert default categories if none exist
    cur.execute("SELECT COUNT(*) FROM categories")
    category_count = cur.fetchone()[0]
    
    if category_count == 0:
        # Insert default categories
        default_categories = [
            ("Electronics", "Electronic devices and accessories"),
            ("Clothing", "Apparel and fashion items"),
            ("Furniture", "Home and office furniture"),
            ("Books", "Books, textbooks, and literature"),
            ("Sports & Outdoors", "Sporting goods and outdoor equipment"),
            ("Home & Kitchen", "Household and kitchen items"),
            ("Toys & Games", "Toys, games, and entertainment items"),
            ("Beauty & Health", "Beauty products and health items"),
            ("Other", "Miscellaneous items")
        ]
        
        for name, description in default_categories:
            cur.execute("""
                INSERT INTO categories (name, description)
                VALUES (%s, %s)
            """, (name, description))
        
        con.commit()
        print("Created default categories")

    # Modify items table to reference category_id instead of storing category name
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
            category_id INT,
            contact_preference VARCHAR(50),
            location VARCHAR(255),
            image_data LONGBLOB,
            FOREIGN KEY (seller_id) REFERENCES users(user_id),
            FOREIGN KEY (category_id) REFERENCES categories(category_id)
        );
    """)

    # Create transactions table to track sales
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id INT AUTO_INCREMENT PRIMARY KEY,
            item_id INT NOT NULL,
            seller_id INT NOT NULL,
            buyer_id INT NOT NULL,
            transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            price DECIMAL(10, 2) NOT NULL,
            status VARCHAR(50) DEFAULT 'Completed',
            payment_method VARCHAR(50),
            notes TEXT,
            FOREIGN KEY (item_id) REFERENCES items(item_id),
            FOREIGN KEY (seller_id) REFERENCES users(user_id),
            FOREIGN KEY (buyer_id) REFERENCES users(user_id)
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
    
    # Check for categories table
    try:
        cur.execute("SHOW TABLES LIKE 'categories'")
        if not cur.fetchone():
            # Create categories table if it doesn't exist
            cur.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    category_id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    parent_category_id INT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (parent_category_id) REFERENCES categories(category_id) ON DELETE SET NULL
                );
            """)
            
            # Insert default categories
            default_categories = [
                ("Electronics", "Electronic devices and accessories"),
                ("Clothing", "Apparel and fashion items"),
                ("Furniture", "Home and office furniture"),
                ("Books", "Books, textbooks, and literature"),
                ("Sports & Outdoors", "Sporting goods and outdoor equipment"),
                ("Home & Kitchen", "Household and kitchen items"),
                ("Toys & Games", "Toys, games, and entertainment items"),
                ("Beauty & Health", "Beauty products and health items"),
                ("Other", "Miscellaneous items")
            ]
            
            for name, description in default_categories:
                cur.execute("""
                    INSERT INTO categories (name, description)
                    VALUES (%s, %s)
                """, (name, description))
            
            con.commit()
            print("Created categories table with default categories")
    except Exception as e:
        print(f"Error checking categories table: {e}")
    
    # Check for transactions table
    try:
        cur.execute("SHOW TABLES LIKE 'transactions'")
        if not cur.fetchone():
            # Create transactions table if it doesn't exist
            cur.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
                    item_id INT NOT NULL,
                    seller_id INT NOT NULL,
                    buyer_id INT NOT NULL,
                    transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    price DECIMAL(10, 2) NOT NULL,
                    status VARCHAR(50) DEFAULT 'Completed',
                    payment_method VARCHAR(50),
                    notes TEXT,
                    FOREIGN KEY (item_id) REFERENCES items(item_id),
                    FOREIGN KEY (seller_id) REFERENCES users(user_id),
                    FOREIGN KEY (buyer_id) REFERENCES users(user_id)
                );
            """)
            con.commit()
            print("Created transactions table")
    except Exception as e:
        print(f"Error checking transactions table: {e}")
    
    # Check for missing columns in items table
    cur.execute("SHOW COLUMNS FROM items")
    existing_item_columns = [column[0] for column in cur.fetchall()]
    
    # If category column exists but category_id doesn't, add category_id
    if "category_id" not in existing_item_columns:
        try:
            cur.execute("ALTER TABLE items ADD COLUMN category_id INT")
            cur.execute("ALTER TABLE items ADD FOREIGN KEY (category_id) REFERENCES categories(category_id)")
            
            # Try to migrate existing category names to category_id values
            if "category" in existing_item_columns:
                # Get all items with categories
                cur.execute("SELECT item_id, category FROM items WHERE category IS NOT NULL")
                items_with_categories = cur.fetchall()
                
                # Update each item's category_id based on category name
                for item_id, category_name in items_with_categories:
                    # Find the category_id for this category name
                    cur.execute("SELECT category_id FROM categories WHERE name = %s", (category_name,))
                    category_result = cur.fetchone()
                    
                    if category_result:
                        category_id = category_result[0]
                        # Update the item's category_id
                        cur.execute("UPDATE items SET category_id = %s WHERE item_id = %s", 
                                    (category_id, item_id))
            
            con.commit()
            print("Added category_id column to items table")
        except Exception as e:
            print(f"Error adding category_id column: {e}")
    
    # Add other missing columns to items table
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

#!/usr/bin/env python3
"""
create_indexes.py - Create optimized indexes for the SecondHand Market database

This script creates the recommended indexes for the SecondHand Market database
as documented in database_indexes.md. The indexes are designed to optimize
query performance for common operations while minimizing maintenance overhead.

Usage:
    python create_indexes.py

The script will:
1. Connect to the database
2. Create the recommended indexes if they don't exist
3. Check and display all indexes in the database
"""

import os
import mysql.connector
from mysql.connector import Error
from tabulate import tabulate

def get_connection():
    """
    Establish a connection to the MySQL database using environment variables
    or default values for connection parameters.
    
    Returns:
        mysql.connector.connection.MySQLConnection: Database connection object
    """
    try:
        connection = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'root'),
            password=os.environ.get('DB_PASSWORD', 'password'),
            database=os.environ.get('DB_NAME', 'secondhand_market')
        )
        if connection.is_connected():
            print(f"Connected to MySQL database: {connection.database}")
            return connection
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None

def create_items_indexes(connection):
    """
    Create indexes on the items table for optimizing common query patterns.
    
    Args:
        connection: MySQL database connection
        
    Returns:
        bool: True if successful, False otherwise
    """
    cursor = connection.cursor()
    indexes = [
        ("status_created_at_idx", "CREATE INDEX status_created_at_idx ON items(status, created_at DESC)"),
        ("category_price_condition_idx", "CREATE INDEX category_price_condition_idx ON items(category_id, price, condition_status)"),
        ("seller_id_idx", "CREATE INDEX seller_id_idx ON items(seller_id)"),
        ("created_at_idx", "CREATE INDEX created_at_idx ON items(created_at)")
    ]
    
    success = True
    for name, sql in indexes:
        try:
            print(f"Creating index: {name}")
            cursor.execute(sql)
            print(f"✓ Index {name} created successfully")
        except Error as e:
            if "Duplicate key name" in str(e):
                print(f"ℹ Index {name} already exists")
            else:
                print(f"✗ Error creating index {name}: {e}")
                success = False
    
    cursor.close()
    return success

def create_categories_indexes(connection):
    """
    Create indexes on the categories table for optimizing hierarchical navigation.
    
    Args:
        connection: MySQL database connection
        
    Returns:
        bool: True if successful, False otherwise
    """
    cursor = connection.cursor()
    try:
        print("Creating index: parent_category_id_idx")
        cursor.execute("CREATE INDEX parent_category_id_idx ON categories(parent_category_id)")
        print("✓ Index parent_category_id_idx created successfully")
        success = True
    except Error as e:
        if "Duplicate key name" in str(e):
            print("ℹ Index parent_category_id_idx already exists")
            success = True
        else:
            print(f"✗ Error creating index parent_category_id_idx: {e}")
            success = False
    
    cursor.close()
    return success

def create_transactions_indexes(connection):
    """
    Create indexes on the transactions table for optimizing transaction queries.
    
    Args:
        connection: MySQL database connection
        
    Returns:
        bool: True if successful, False otherwise
    """
    cursor = connection.cursor()
    indexes = [
        ("item_id_idx", "CREATE INDEX item_id_idx ON transactions(item_id)"),
        ("seller_id_idx", "CREATE INDEX seller_id_idx ON transactions(seller_id)"),
        ("buyer_id_idx", "CREATE INDEX buyer_id_idx ON transactions(buyer_id)"),
        ("transaction_date_idx", "CREATE INDEX transaction_date_idx ON transactions(transaction_date)")
    ]
    
    success = True
    for name, sql in indexes:
        try:
            print(f"Creating index: {name}")
            cursor.execute(sql)
            print(f"✓ Index {name} created successfully")
        except Error as e:
            if "Duplicate key name" in str(e):
                print(f"ℹ Index {name} already exists")
            else:
                print(f"✗ Error creating index {name}: {e}")
                success = False
    
    cursor.close()
    return success

def check_indexes(connection, database_name=None):
    """
    Check and display all indexes in the database.
    
    Args:
        connection: MySQL database connection
        database_name: Name of the database to check (optional)
        
    Returns:
        None
    """
    cursor = connection.cursor()
    
    if not database_name:
        database_name = connection.database
    
    try:
        print("\n=== Current Database Indexes ===")
        
        # Get a list of tables in the database
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        
        index_data = []
        
        # For each table, get its indexes
        for table in tables:
            cursor.execute(f"SHOW INDEX FROM {table}")
            indexes = cursor.fetchall()
            
            for index in indexes:
                # Extract relevant fields (index name, column name, etc.)
                table_name = index[0]
                index_name = index[2]
                column_name = index[4]
                non_unique = "Non-unique" if index[1] == 1 else "Unique"
                
                index_data.append([table_name, index_name, column_name, non_unique])
        
        # Sort the data by table name and index name
        index_data.sort(key=lambda x: (x[0], x[1]))
        
        # Display the index information in a tabulated format
        if index_data:
            headers = ["Table", "Index Name", "Column", "Type"]
            print(tabulate(index_data, headers=headers, tablefmt="grid"))
        else:
            print("No indexes found in the database.")
    
    except Error as e:
        print(f"Error checking indexes: {e}")
    
    cursor.close()

def main():
    """
    Main function to create and check database indexes.
    """
    connection = get_connection()
    if not connection:
        return
    
    try:
        # Create indexes for each table
        items_success = create_items_indexes(connection)
        categories_success = create_categories_indexes(connection)
        transactions_success = create_transactions_indexes(connection)
        
        # Check and display all indexes
        check_indexes(connection)
        
        # Commit changes
        connection.commit()
        
        # Summary
        print("\n=== Index Creation Summary ===")
        print(f"Items table indexes: {'✓ Success' if items_success else '✗ Some errors occurred'}")
        print(f"Categories table indexes: {'✓ Success' if categories_success else '✗ Some errors occurred'}")
        print(f"Transactions table indexes: {'✓ Success' if transactions_success else '✗ Some errors occurred'}")
        
        all_success = items_success and categories_success and transactions_success
        if all_success:
            print("\n✅ All recommended indexes created successfully!")
        else:
            print("\n⚠️ Some indexes could not be created. Check the logs above for details.")
    
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    
    finally:
        # Close the connection
        if connection and connection.is_connected():
            connection.close()
            print("\nDatabase connection closed.")

if __name__ == "__main__":
    main() 
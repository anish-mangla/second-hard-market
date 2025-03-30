# secondhand_market/database/transaction_manager.py

import mysql.connector
from contextlib import contextmanager
from database.db_setup import get_connection
from sqlalchemy.orm import Session
from sqlalchemy import event
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define isolation levels
class IsolationLevel:
    """Constants for MySQL isolation levels"""
    READ_UNCOMMITTED = "READ UNCOMMITTED"
    READ_COMMITTED = "READ COMMITTED"
    REPEATABLE_READ = "REPEATABLE READ"  # MySQL default
    SERIALIZABLE = "SERIALIZABLE"

@contextmanager
def transaction(isolation_level=IsolationLevel.REPEATABLE_READ):
    """
    Context manager for handling transactions with specified isolation level.
    
    Args:
        isolation_level: The transaction isolation level to use
        
    Yields:
        connection: The database connection with active transaction
        cursor: A cursor for executing SQL statements
        
    Example:
        with transaction(IsolationLevel.READ_COMMITTED) as (conn, cursor):
            cursor.execute("UPDATE items SET status = 'Sold' WHERE item_id = %s", (item_id,))
    """
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        # Set the isolation level for this transaction
        cursor.execute(f"SET TRANSACTION ISOLATION LEVEL {isolation_level}")
        
        # Start transaction
        connection.start_transaction()
        logger.info(f"Transaction started with isolation level: {isolation_level}")
        
        yield connection, cursor
        
        # If no exceptions, commit the transaction
        connection.commit()
        logger.info("Transaction committed successfully")
        
    except Exception as e:
        # On error, roll back the transaction
        connection.rollback()
        logger.error(f"Transaction rolled back due to error: {str(e)}")
        raise
    
    finally:
        # Always close cursor and connection
        cursor.close()
        connection.close()

@contextmanager
def sqlalchemy_transaction(session, isolation_level=IsolationLevel.REPEATABLE_READ):
    """
    Context manager for handling SQLAlchemy ORM transactions with specified isolation level.
    
    Args:
        session: SQLAlchemy session
        isolation_level: The transaction isolation level to use
        
    Yields:
        session: The SQLAlchemy session with active transaction
        
    Example:
        from database.orm_models import get_session
        session = get_session()
        with sqlalchemy_transaction(session, IsolationLevel.SERIALIZABLE) as session:
            new_item = Item(title="Example", price=10.99)
            session.add(new_item)
    """
    # Set isolation level
    session.execute(f"SET TRANSACTION ISOLATION LEVEL {isolation_level}")
    
    try:
        # The transaction is already started by SQLAlchemy
        logger.info(f"SQLAlchemy transaction started with isolation level: {isolation_level}")
        
        yield session
        
        # Commit if no exceptions
        session.commit()
        logger.info("SQLAlchemy transaction committed successfully")
        
    except Exception as e:
        # Rollback on error
        session.rollback()
        logger.error(f"SQLAlchemy transaction rolled back due to error: {str(e)}")
        raise
    
    finally:
        # Close the session
        session.close()

# Demonstration function for concurrent item status update
def update_item_status_safely(item_id, new_status, isolation_level=IsolationLevel.SERIALIZABLE):
    """
    Updates an item's status with proper transaction handling to prevent conflicts.
    
    This function uses SERIALIZABLE isolation to prevent lost updates in concurrent scenarios.
    
    Args:
        item_id: ID of the item to update
        new_status: New status value ('Available', 'Pending', 'Sold')
        isolation_level: Transaction isolation level
    
    Returns:
        bool: True if update was successful, False if item was already updated by another user
    """
    with transaction(isolation_level) as (conn, cursor):
        # First check current status
        cursor.execute("SELECT status FROM items WHERE item_id = %s FOR UPDATE", (item_id,))
        result = cursor.fetchone()
        
        if not result:
            return False  # Item doesn't exist
            
        current_status = result['status']
        
        # Implement business logic for allowed status transitions
        if current_status == 'Sold' and new_status != 'Sold':
            logger.warning(f"Cannot change status of sold item {item_id}")
            return False
        
        # If status is "Pending", only the same user who set it to pending should be able to update
        # In a real app, you'd include user_id in this check
        
        # Update the status
        cursor.execute(
            "UPDATE items SET status = %s WHERE item_id = %s",
            (new_status, item_id)
        )
        
        # Check if row was actually updated
        return cursor.rowcount > 0

# Demonstration function for concurrent item purchase
def purchase_item(item_id, buyer_id, isolation_level=IsolationLevel.SERIALIZABLE):
    """
    Purchases an item with proper transaction handling to prevent conflicts.
    
    Uses SERIALIZABLE isolation to ensure the item isn't purchased by multiple buyers.
    
    Args:
        item_id: ID of the item to purchase
        buyer_id: ID of the buyer
        isolation_level: Transaction isolation level
    
    Returns:
        bool: True if purchase was successful, False if item was already sold/pending
    """
    with transaction(isolation_level) as (conn, cursor):
        # Check if item is available, using FOR UPDATE to lock the row
        cursor.execute(
            "SELECT status, price, seller_id FROM items WHERE item_id = %s FOR UPDATE", 
            (item_id,)
        )
        item = cursor.fetchone()
        
        if not item:
            logger.warning(f"Item {item_id} not found")
            return False
            
        if item['status'] != 'Available':
            logger.warning(f"Item {item_id} is not available for purchase (status: {item['status']})")
            return False
            
        # Update item status to Sold
        cursor.execute(
            "UPDATE items SET status = 'Sold' WHERE item_id = %s",
            (item_id,)
        )
        
        # Record the purchase in a transaction table (would create this in a real app)
        # cursor.execute(
        #     "INSERT INTO transactions (item_id, buyer_id, seller_id, price, transaction_date) "
        #     "VALUES (%s, %s, %s, %s, NOW())",
        #     (item_id, buyer_id, item['seller_id'], item['price'])
        # )
        
        logger.info(f"Item {item_id} purchased successfully by user {buyer_id}")
        return True 
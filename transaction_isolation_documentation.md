# Database Transaction Management and Isolation Levels

## Overview

This document explains how database transactions and isolation levels are implemented in the SecondHand Market application to handle concurrent user access. While the current application is primarily designed for single-user operation, this implementation prepares it for multi-user scenarios by preventing common concurrency issues.

## What are Transactions and Isolation Levels?

### Transactions

A transaction is a sequence of operations performed as a single logical unit of work. A transaction has four key properties (ACID):

- **Atomicity**: All operations in a transaction succeed or fail together
- **Consistency**: A transaction transforms the database from one consistent state to another
- **Isolation**: Concurrent transactions don't interfere with each other
- **Durability**: Once committed, changes persist even in system failure

### Isolation Levels

Isolation levels determine how transaction integrity is visible to other users and systems. They control what kind of concurrency phenomena can occur:

1. **READ UNCOMMITTED**: Lowest isolation. Transactions can see uncommitted changes from other transactions ("dirty reads").
   
2. **READ COMMITTED**: Transactions can only see changes from other committed transactions, but non-repeatable reads can occur.
   
3. **REPEATABLE READ**: Same data is seen throughout the transaction even if others change and commit it, but phantom reads can occur.
   
4. **SERIALIZABLE**: Highest isolation. Transactions are completely isolated from each other, as if they were executed serially.

## Implementation in SecondHand Market

### Architecture

The transaction system is implemented in `database/transaction_manager.py` with two main components:

1. **Context Managers**: Python context managers (`with` statements) that handle transaction lifecycles
2. **Isolation Level Configuration**: Ability to set different isolation levels per transaction
3. **Helper Functions**: Business logic for common transaction scenarios

### Key Components

#### 1. Isolation Level Constants

```python
class IsolationLevel:
    """Constants for MySQL isolation levels"""
    READ_UNCOMMITTED = "READ UNCOMMITTED"
    READ_COMMITTED = "READ COMMITTED"
    REPEATABLE_READ = "REPEATABLE READ"  # MySQL default
    SERIALIZABLE = "SERIALIZABLE"
```

#### 2. Transaction Context Manager

```python
@contextmanager
def transaction(isolation_level=IsolationLevel.REPEATABLE_READ):
    """Context manager for handling transactions with specified isolation level."""
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        # Set isolation level and start transaction
        cursor.execute(f"SET TRANSACTION ISOLATION LEVEL {isolation_level}")
        connection.start_transaction()
        
        yield connection, cursor
        
        # Commit on success
        connection.commit()
        
    except Exception as e:
        # Rollback on error
        connection.rollback()
        raise
    finally:
        # Always clean up
        cursor.close()
        connection.close()
```

#### 3. SQLAlchemy ORM Transaction Manager

```python
@contextmanager
def sqlalchemy_transaction(session, isolation_level=IsolationLevel.REPEATABLE_READ):
    """Context manager for SQLAlchemy ORM transactions with specified isolation level."""
    # Set isolation level
    session.execute(f"SET TRANSACTION ISOLATION LEVEL {isolation_level}")
    
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()
```

## Concurrency Scenarios and Solutions

### 1. Lost Updates

**Problem**: Two users edit the same item simultaneously, and one user's changes overwrite the other's.

**Solution**: The application uses `REPEATABLE READ` isolation for edit operations and row locking with `SELECT ... FOR UPDATE`:

```python
# First check and lock the record
cursor.execute("SELECT status FROM items WHERE item_id = %s FOR UPDATE", (item_id,))
```

### 2. Double Booking (Item Purchase)

**Problem**: Two users attempt to purchase the same item at the same time.

**Solution**: The application uses `SERIALIZABLE` isolation and explicit checking:

```python
with transaction(IsolationLevel.SERIALIZABLE) as (conn, cursor):
    # Check and lock the item
    cursor.execute("SELECT status FROM items WHERE item_id = %s FOR UPDATE", (item_id,))
    item = cursor.fetchone()
    
    if item['status'] != 'Available':
        return False  # Already purchased or pending
    
    # Update status to Sold
    cursor.execute("UPDATE items SET status = 'Sold' WHERE item_id = %s", (item_id,))
```

### 3. Phantom Reads in Reports

**Problem**: Reports showing inconsistent data when items are added/removed during report generation.

**Solution**: Use `SERIALIZABLE` isolation for complex reports:

```python
with transaction(IsolationLevel.SERIALIZABLE) as (conn, cursor):
    # Multiple related queries will see a consistent snapshot
    cursor.execute("SELECT COUNT(*) FROM items WHERE status = 'Available'")
    cursor.execute("SELECT AVG(price) FROM items WHERE status = 'Available'")
```

## Isolation Level Selection Guidelines

The application uses different isolation levels based on operation requirements:

1. **READ COMMITTED** (Default for read-only operations):
   - Simple lookups and searches
   - Non-critical reports
   - When performance is more important than absolute consistency

2. **REPEATABLE READ** (Default for most write operations):
   - Item edits
   - User profile updates
   - When consistent reads are required during a transaction

3. **SERIALIZABLE** (For critical operations):
   - Item purchases
   - Item deletions
   - Financial transactions 
   - When strong data integrity guarantees are required

## Multi-User Considerations

For a fully multi-user version of the application:

1. **User Authentication**: Each transaction would be associated with a specific user
2. **Row-Level Permissions**: Check if the current user has permission to modify data
3. **Optimistic Locking**: Add version columns to detect concurrent modifications
4. **Deadlock Handling**: Implement retry logic for deadlocks
5. **Connection Pooling**: Efficiently manage database connections across users

## Performance Considerations

Transaction isolation has performance implications:

- Higher isolation levels reduce concurrency and may impact performance
- Use the appropriate level for each operation
- Consider timeouts for long-running transactions
- Monitor and optimize database locks

## Conclusion

The transaction management system in the SecondHand Market application provides a solid foundation for handling concurrent operations. By implementing proper isolation levels and transaction handling, the application maintains data consistency even when multiple users interact with the same data simultaneously. 
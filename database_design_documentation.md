# SecondHand Market - Database Design Documentation

## Table of Contents
1. [Overview](#overview)
2. [Entity-Relationship Diagram](#entity-relationship-diagram)
3. [Database Schema](#database-schema)
4. [Table Relationships](#table-relationships)
5. [Normalization](#normalization)
6. [Stored Procedures](#stored-procedures)
7. [Indexing Strategy](#indexing-strategy)
8. [Transaction Management](#transaction-management)
9. [Data Access Methods](#data-access-methods)
10. [Query Optimization](#query-optimization)
11. [Schema Evolution](#schema-evolution)

## Overview

The SecondHand Market application uses a relational database (MySQL) to store and manage all data related to users, items, categories, and transactions. The database is designed to efficiently support the core functionality of a marketplace platform while ensuring data integrity, security, and performance.

### Design Goals

- **Scalability**: Support for growing number of users, items, and transactions
- **Performance**: Optimized for frequent read operations (browsing listings)
- **Data Integrity**: Proper foreign key constraints and validation
- **Flexibility**: Support for various item types and categories
- **Maintainability**: Clear structure and documentation

## Entity-Relationship Diagram

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│    Users    │       │    Items    │       │ Categories  │
├─────────────┤       ├─────────────┤       ├─────────────┤
│ PK: user_id │◄──┐   │ PK: item_id │       │PK: category_│
│ username    │   │   │ title       │       │    id       │
│ email       │   │   │ description │       │ name        │
│ phone       │   │   │ price       │       │ description │
│ password    │   │   │ condition   │       │ parent_cat  │◄─┐
└─────────────┘   │   │ FK: seller_id│───────┐            │  │
                  │   │ FK: category_│───────┘ └──────────┘  │
                  │   │ status      │          │             │
                  │   │ created_at  │          └─────────────┘
                  │   └─────────────┘                
                  │           │
                  │           │
                  │           ▼
                  │   ┌───────────────┐
                  │   │ Transactions  │
                  │   ├───────────────┤
                  │   │PK: transaction│
                  │   │    _id        │
                  └───┤FK: seller_id  │
                  ┌───┤FK: buyer_id   │
                  │   │FK: item_id    │
                  │   │transaction_date│
                  │   │price          │
                  │   │status         │
                  │   │payment_method │
                  └───┤notes          │
                      └───────────────┘
```

## Database Schema

### Users Table

Stores user account information for buyers and sellers.

| Column Name   | Data Type      | Constraints       | Description                     |
|---------------|----------------|-------------------|---------------------------------|
| user_id       | INT            | PK, AUTO_INCREMENT| Unique identifier for each user |
| username      | VARCHAR(100)   | NOT NULL          | User's display name             |
| email         | VARCHAR(255)   |                   | User's email address            |
| phone         | VARCHAR(50)    |                   | User's phone number             |
| password_hash | VARCHAR(255)   |                   | Hashed user password            |

### Categories Table

Stores product categories with support for hierarchical categorization.

| Column Name       | Data Type      | Constraints      | Description                       |
|-------------------|----------------|------------------|-----------------------------------|
| category_id       | INT            | PK, AUTO_INCREMENT| Unique identifier for category    |
| name              | VARCHAR(100)   | NOT NULL         | Category name                     |
| description       | TEXT           |                  | Category description              |
| parent_category_id| INT            | FK               | Parent category (for hierarchical structure) |
| created_at        | DATETIME       | DEFAULT NOW()    | When category was created         |

### Items Table

Stores listing information for items being sold on the marketplace.

| Column Name       | Data Type      | Constraints      | Description                        |
|-------------------|----------------|------------------|------------------------------------|
| item_id           | INT            | PK, AUTO_INCREMENT| Unique identifier for item         |
| title             | VARCHAR(255)   | NOT NULL         | Item title/name                    |
| description       | TEXT           |                  | Detailed item description          |
| price             | DECIMAL(10,2)  |                  | Item price                         |
| condition_status  | VARCHAR(50)    |                  | Item condition (New, Used, etc.)   |
| created_at        | DATETIME       | DEFAULT NOW()    | When listing was created           |
| status            | VARCHAR(50)    | DEFAULT 'Available'| Item status (Available, Sold, etc.)|
| seller_id         | INT            | FK               | Reference to user who listed item  |
| category_id       | INT            | FK               | Reference to item category         |
| contact_preference| VARCHAR(50)    |                  | Preferred contact method           |
| location          | VARCHAR(255)   |                  | Item location                      |
| image_data        | LONGBLOB       |                  | Item image                         |

### Transactions Table

Records completed sales between users.

| Column Name       | Data Type      | Constraints      | Description                        |
|-------------------|----------------|------------------|------------------------------------|
| transaction_id    | INT            | PK, AUTO_INCREMENT| Unique transaction identifier      |
| item_id           | INT            | FK, NOT NULL     | Reference to sold item             |
| seller_id         | INT            | FK, NOT NULL     | Reference to seller                |
| buyer_id          | INT            | FK, NOT NULL     | Reference to buyer                 |
| transaction_date  | DATETIME       | DEFAULT NOW()    | When transaction occurred          |
| price             | DECIMAL(10,2)  | NOT NULL         | Final sale price                   |
| status            | VARCHAR(50)    | DEFAULT 'Completed'| Transaction status                |
| payment_method    | VARCHAR(50)    |                  | Method of payment                  |
| notes             | TEXT           |                  | Additional transaction notes       |

## Table Relationships

### One-to-Many Relationships

1. **Users to Items**: One user can list many items (seller_id in items table)
2. **Categories to Items**: One category can contain many items (category_id in items table)
3. **Categories to Categories**: One category can have many subcategories (parent_category_id)

### Many-to-One Relationships

1. **Items to Users**: Many items can be listed by one user
2. **Items to Categories**: Many items can belong to one category

### One-to-Many Relationships with Transactions

1. **Users to Transactions (as seller)**: One user can sell many items
2. **Users to Transactions (as buyer)**: One user can buy many items
3. **Items to Transactions**: One item can have one transaction (when sold)

## Normalization

The database schema follows normalization principles to minimize redundancy and dependency:

### First Normal Form (1NF)
- All tables have primary keys
- All columns contain atomic values (no multi-valued attributes)
- No repeating groups

### Second Normal Form (2NF)
- All tables are in 1NF
- All non-key attributes fully depend on the primary key
  - For example, item details depend only on item_id

### Third Normal Form (3NF)
- All tables are in 2NF
- No transitive dependencies
  - For example, category details are stored in a separate categories table rather than duplicating this information in the items table

### Benefits of Normalization in this Design:
- Reduced data redundancy (e.g., category information stored once)
- Improved data integrity (e.g., updating a category name affects all items in that category)
- Easier maintenance and extension

## Stored Procedures

The application uses several stored procedures to encapsulate complex database operations:

### 1. get_marketplace_stats
```sql
CREATE PROCEDURE get_marketplace_stats(IN start_date_param VARCHAR(20), IN end_date_param VARCHAR(20))
BEGIN
    SELECT 
        COUNT(*) AS total_items,
        SUM(CASE WHEN status = 'Available' THEN 1 ELSE 0 END) AS available_count,
        SUM(CASE WHEN status = 'Sold' THEN 1 ELSE 0 END) AS sold_count,
        ROUND(AVG(price), 2) AS avg_price
    FROM items
    WHERE (start_date_param IS NULL OR created_at >= start_date_param)
    AND (end_date_param IS NULL OR created_at <= end_date_param);
END
```

### 2. category_analysis
```sql
CREATE PROCEDURE category_analysis(IN start_date_param VARCHAR(20), IN end_date_param VARCHAR(20))
BEGIN
    SELECT 
        c.name AS category,
        COUNT(i.item_id) AS item_count,
        ROUND(AVG(i.price), 2) AS avg_price,
        COUNT(CASE WHEN i.status = 'Sold' THEN 1 ELSE NULL END) AS sold_count
    FROM items i
    JOIN categories c ON i.category_id = c.category_id
    WHERE (start_date_param IS NULL OR i.created_at >= start_date_param)
    AND (end_date_param IS NULL OR i.created_at <= end_date_param)
    GROUP BY c.category_id
    ORDER BY item_count DESC;
END
```

### 3. price_distribution
```sql
CREATE PROCEDURE price_distribution()
BEGIN
    SELECT 
        CASE
            WHEN price BETWEEN 0 AND 10 THEN '$0-$10'
            WHEN price BETWEEN 10 AND 25 THEN '$10-$25'
            WHEN price BETWEEN 25 AND 50 THEN '$25-$50'
            WHEN price BETWEEN 50 AND 100 THEN '$50-$100'
            WHEN price BETWEEN 100 AND 250 THEN '$100-$250'
            WHEN price BETWEEN 250 AND 500 THEN '$250-$500'
            WHEN price > 500 THEN '$500+'
            ELSE 'Unknown'
        END AS price_range,
        COUNT(*) AS item_count
    FROM items
    GROUP BY price_range;
END
```

### 4. get_items_by_filter
```sql
CREATE PROCEDURE get_items_by_filter(
    IN category_id_param INT,
    IN min_price_param DECIMAL(10, 2),
    IN max_price_param DECIMAL(10, 2),
    IN condition_param VARCHAR(50),
    IN status_param VARCHAR(50)
)
BEGIN
    SELECT i.*, u.username, u.email, c.name as category 
    FROM items i 
    LEFT JOIN users u ON i.seller_id = u.user_id 
    LEFT JOIN categories c ON i.category_id = c.category_id
    WHERE 1=1
        AND (category_id_param IS NULL OR i.category_id = category_id_param)
        AND (i.price BETWEEN min_price_param AND max_price_param)
        AND (condition_param IS NULL OR condition_param = '' OR condition_param = 'All Conditions' OR i.condition_status = condition_param)
        AND (status_param IS NULL OR status_param = '' OR i.status = status_param)
    ORDER BY i.created_at DESC;
END
```

### 5. get_transaction_history
```sql
CREATE PROCEDURE get_transaction_history(
    IN start_date_param DATE,
    IN end_date_param DATE,
    IN seller_id_param INT,
    IN buyer_id_param INT
)
BEGIN
    SELECT t.*, 
           i.title as item_title, 
           s.username as seller_name,
           b.username as buyer_name
    FROM transactions t
    JOIN items i ON t.item_id = i.item_id
    JOIN users s ON t.seller_id = s.user_id
    JOIN users b ON t.buyer_id = b.user_id
    WHERE (start_date_param IS NULL OR DATE(t.transaction_date) >= start_date_param)
      AND (end_date_param IS NULL OR DATE(t.transaction_date) <= end_date_param)
      AND (seller_id_param IS NULL OR t.seller_id = seller_id_param)
      AND (buyer_id_param IS NULL OR t.buyer_id = buyer_id_param)
    ORDER BY t.transaction_date DESC;
END
```

## Indexing Strategy

The database uses the following indexing strategy to improve query performance:

1. **Primary Key Indexes**: All tables have primary key indexes (user_id, item_id, category_id, transaction_id)

2. **Foreign Key Indexes**: Indexes on all foreign key columns to speed up joins:
   - seller_id, category_id in items table
   - seller_id, buyer_id, item_id in transactions table
   - parent_category_id in categories table

3. **Additional Indexes**:
   - items(status) - Frequently filtered by item status
   - items(created_at) - Used for sorting and date filtering
   - items(price) - Used for price range filtering

## Transaction Management

The application implements transaction management to ensure data consistency:

### Transaction Isolation Levels

Different operations use appropriate isolation levels:

1. **READ COMMITTED** (Default): Used for most read operations (viewing items, reports)
   - Prevents dirty reads but allows non-repeatable reads
   - Good balance of consistency and performance

2. **REPEATABLE READ**: Used for financial transactions
   - Prevents dirty reads and non-repeatable reads
   - Ensures consistency during transaction processing

3. **SERIALIZABLE**: Used for critical reports
   - Highest isolation level
   - Prevents dirty reads, non-repeatable reads, and phantom reads

### Transaction Manager Implementation

The application includes a transaction manager that:
- Opens and manages database connections within transactions
- Sets appropriate isolation levels
- Handles commits and rollbacks
- Includes error handling and recovery

## Data Access Methods

The application employs multiple data access methods:

### 1. Direct SQL Queries with Prepared Statements

Used for simple CRUD operations and performance-critical code.

```python
cursor.execute(
    "INSERT INTO items (title, description, price, seller_id) VALUES (%s, %s, %s, %s)",
    (title, description, price, seller_id)
)
```

### 2. ORM (SQLAlchemy)

Used for complex object relationships and maintainable code.

```python
# ORM Model definitions
class Item(Base):
    __tablename__ = 'items'
    
    item_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(Numeric(10, 2))
    # ... other fields ...
    
    # Relationships
    seller = relationship("User", back_populates="items")
    category = relationship("Category", back_populates="items")
```

### 3. Stored Procedures

Used for complex queries and server-side processing.

```python
cursor.execute("CALL get_marketplace_stats(%s, %s)", [start_date, end_date])
stats = cursor.fetchone()
```

## Query Optimization

The database queries are optimized using several techniques:

### 1. Efficient JOIN Operations

```sql
-- Efficient join with proper indexing on foreign keys
SELECT i.*, u.username, c.name 
FROM items i 
LEFT JOIN users u ON i.seller_id = u.user_id 
LEFT JOIN categories c ON i.category_id = c.category_id
WHERE i.status = 'Available';
```

### 2. Selective Column Selection

```sql
-- Only select needed columns rather than SELECT *
SELECT item_id, title, price, created_at 
FROM items 
WHERE status = 'Available';
```

### 3. Appropriate WHERE Clause Ordering

```sql
-- Place most selective conditions first
SELECT * FROM items 
WHERE seller_id = 1         -- More selective (if properly indexed)
  AND status = 'Available'  -- Less selective
  AND price > 10;           -- Medium selectivity
```

### 4. Pagination for Large Result Sets

```sql
-- Limit result sets to improve performance
SELECT * FROM items 
WHERE status = 'Available' 
ORDER BY created_at DESC 
LIMIT 20 OFFSET 40;
```

## Schema Evolution

The database includes mechanisms for non-destructive schema updates:

### 1. Schema Version Tracking

The application tracks schema versions and applies updates as needed.

### 2. Migration Logic

The `check_and_update_schema()` function in `db_setup.py` checks for and applies necessary schema changes:

```python
def check_and_update_schema():
    """
    Checks if the database schema needs updates and applies them if needed.
    This allows for non-destructive schema updates after initial creation.
    """
    # Check for new tables
    # Add missing columns
    # Update column types if needed
    # Add new constraints
    # ...
```

### Examples of Schema Evolution:

1. **Adding New Columns**:
   ```sql
   ALTER TABLE items ADD COLUMN contact_preference VARCHAR(50);
   ```

2. **Adding New Tables**:
   ```sql
   CREATE TABLE IF NOT EXISTS transactions (...);
   ```

3. **Migrating Data**:
   ```python
   # When adding category_id to replace category string
   cur.execute("SELECT item_id, category FROM items WHERE category IS NOT NULL")
   for item_id, category_name in cur.fetchall():
       cur.execute("SELECT category_id FROM categories WHERE name = %s", (category_name,))
       category_id = cur.fetchone()[0]
       cur.execute("UPDATE items SET category_id = %s WHERE item_id = %s", 
                   (category_id, item_id))
   ```

---

This database design document provides a comprehensive overview of the SecondHand Market database architecture, including schema design, relationships, optimization strategies, and evolution mechanisms. The design focuses on balancing performance, data integrity, and maintainability to support the application's requirements. 
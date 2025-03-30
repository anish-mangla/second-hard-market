# Database Access Methods Design Document

## Overview

This document outlines how the SecondHand Market application meets the requirement to use at least two database access methods with specific proportions. The application employs three different database access methods:

1. Prepared Statements (Direct SQL)
2. Object-Relational Mapping (ORM) via SQLAlchemy
3. Stored Procedures

## Implementation Details

### Prepared Statements (≈50%)

Prepared statements are the most commonly used method in the application, serving as the foundation for database access. These are implemented using the `mysql-connector-python` library.

**Examples:**

```python
# Example 1: Retrieving data with prepared statements
cur.execute("SELECT * FROM items WHERE item_id = %s", (item_id,))
item_data = cur.fetchone()

# Example 2: Inserting data with prepared statements
cur.execute("""
    INSERT INTO users (username, email, phone)
    VALUES (%s, %s, %s)
""", (username, email, phone))
con.commit()
```

**Usage Locations:**
- Initial database setup and schema evolution in `database/db_setup.py`
- Most query operations in all three pages
- Filter operations in the View Items page
- Simple aggregation queries

### Object-Relational Mapping (≈30%)

ORM is implemented using SQLAlchemy to provide an object-oriented interface to the database. This approach abstracts the SQL queries and allows for more maintainable code.

**Examples:**

```python
# Example 1: Creating a new item using ORM
new_item = Item(
    title=title,
    description=description,
    price=Decimal(price),
    condition_status=condition_status,
    seller_id=seller_id,
    category=category,
    contact_preference=contact_preference,
    location=location,
    image_data=image_data
)
session.add(new_item)
session.commit()

# Example 2: Querying with ORM
user = session.query(User).filter(User.email == email).first()
```

**Usage Locations:**
- User information retrieval and updates in `pages/1_Create_Item.py`
- Item creation in the Create Item page
- Some parts of the reporting functionality

### Stored Procedures (≈20%)

Stored procedures are used for complex data operations and reports that require significant data processing on the database side. These are defined in `database/create_procedures.py`.

**Examples:**

```python
# Creating a stored procedure
cursor.execute("""
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
""")

# Calling a stored procedure
cur.execute("CALL get_marketplace_stats(%s, %s)", [start_date, end_date])
stats = cur.fetchone()
```

**Usage Locations:**
- Complex reporting in `pages/3_Reports.py`
- Filter operations in `pages/2_View_Items.py` via the `get_items_by_filter` procedure
- Category analysis and price distribution reports

## Dynamic UI Components

The application features numerous dynamic UI components that retrieve data from the database:

1. **Category Dropdown Lists**: Dynamically populated from database categories
   ```python
   cur.execute("SELECT DISTINCT category FROM items WHERE category IS NOT NULL")
   categories = [cat[0] for cat in cur.fetchall()]
   selected_category = st.sidebar.selectbox("Category", ["All Categories"] + categories)
   ```

2. **Price Range Sliders**: Min/max values determined from database data
   ```python
   cur.execute("SELECT MIN(price), MAX(price) FROM items")
   min_price, max_price = cur.fetchone()
   price_range = st.sidebar.slider("Select price range", min_value=min_price, max_value=max_price)
   ```

3. **Status Filters**: Available options determined by database
   ```python
   status_options = ["All", "Available", "Pending", "Sold"]
   selected_status = st.sidebar.selectbox("Status", status_options)
   ```

4. **Dynamic Item Grid**: Populated based on query parameters and filters
   ```python
   cur.execute(query, params)
   items = cur.fetchall()
   # Grid is then populated with these items
   ```

## Benefits of Multiple Methods

1. **Appropriate Method for Each Task**: Each method has strengths for different scenarios
   - Prepared statements: Simple queries, schema management
   - ORM: Object-oriented code, relationships between entities
   - Stored procedures: Complex reports, server-side processing

2. **Code Organization**: Different interfaces for different components
   - Direct database layer for core operations
   - ORM for business logic
   - Stored procedures for reporting

3. **Performance Optimization**: 
   - Stored procedures reduce network traffic for complex queries
   - ORM improves maintainability
   - Prepared statements provide flexibility

4. **Learning Opportunity**: Demonstrates understanding of multiple database access paradigms

## Conclusion

The SecondHand Market application successfully implements the requirement to use multiple database access methods in specific proportions. This mixed approach provides both technical advantages and educational value, demonstrating understanding of different database interaction paradigms. 
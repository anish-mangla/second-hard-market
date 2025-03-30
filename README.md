# SecondHand Market Application

A comprehensive web-based marketplace platform that enables users to buy and sell secondhand items. This project was developed as a database systems course project to demonstrate various database concepts and implementations.

![SecondHand Market](https://cdn-icons-png.flaticon.com/512/3900/3900101.png)

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [Course Requirements Implementation](#course-requirements-implementation)
  - [Dynamic UI Components](#dynamic-ui-components)
  - [Database Access Methods](#database-access-methods)
- [Database Design](#database-design)
  - [Entity Relationship Diagram](#entity-relationship-diagram)
  - [Database Schema](#database-schema)
  - [Normalization](#normalization)
  - [Relationships](#relationships)
  - [Schema Evolution](#schema-evolution)
- [Implementation](#implementation)
- [Query Examples](#query-examples)
- [Setup and Installation](#setup-and-installation)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Future Enhancements](#future-enhancements)

## 🔍 Project Overview

The SecondHand Market application is designed to facilitate the buying and selling of used items within a community. It provides a platform for users to list items they want to sell, browse available listings, and manage their transactions. The project demonstrates core database concepts applied in a real-world scenario.

## ✨ Features

- **User Management**: User registration, profiles, and authentication system
- **Item Listings**: Create, view, edit, and delete secondhand items
- **Image Upload**: Upload and display item images
- **Search & Filter**: Search items by keyword and filter by various criteria
- **Categories**: Browse items by predefined categories
- **Contact Information**: Connect buyers with sellers
- **Analytics Dashboard**: View marketplace trends and statistics
- **Responsive Interface**: User-friendly web interface built with Streamlit

## 🎓 Course Requirements Implementation

### Dynamic UI Components

This project implements dynamic user interface components that are populated from the database:

1. **Category Dropdown**: On the "View Items" page, the category filter dropdown is dynamically populated with all unique categories from the database.
   - Implementation: `pages/2_View_Items.py` fetches distinct categories from the `items` table
   - Code: `cur.execute("SELECT DISTINCT category FROM items WHERE category IS NOT NULL")`

2. **Price Range Slider**: The min and max values for the price range slider are dynamically calculated from the database.
   - Implementation: `pages/2_View_Items.py` determines the price range from actual item prices
   - Code: `cur.execute("SELECT MIN(price), MAX(price) FROM items")`

3. **Item Cards**: All items displayed in the marketplace are dynamically loaded from the database based on user filters.
   - Implementation: Items are fetched using various database access methods (described below)

### Database Access Methods

The application uses a combination of three database access methods, ensuring each method accounts for at least 20% of the database access code:

1. **Prepared Statements (~40% of database access)**
   - All direct SQL queries use parameterized prepared statements for security and performance
   - Example locations:
     - `pages/2_View_Items.py`: Complex filtering and search operations
     - `pages/3_Reports.py`: Weekly items report (line 146-156)
     - `pages/2_View_Items.py`: Edit and delete operations

2. **SQLAlchemy ORM (~30% of database access)**
   - Object-Relational Mapping for a more Pythonic approach to database operations
   - Implementation: `database/orm_models.py` defines the ORM models matching our database schema
   - Used in:
     - `pages/1_Create_Item.py`: All creation operations for new items
     - User management operations (retrieving and updating user information)

3. **Stored Procedures (~30% of database access)**
   - Complex, optimized SQL operations defined in the database
   - Implementation: `database/create_procedures.py` creates the procedures
   - Used in:
     - `pages/3_Reports.py`: All reports and analytics operations
     - `pages/2_View_Items.py`: The filtered item search with the `get_items_by_filter` procedure

This balanced approach demonstrates different database access methodologies and their appropriate use cases, meeting the course requirement of using at least two methods with each accounting for at least 20% of the code.

## 💾 Database Design

### Entity Relationship Diagram

The database design follows this simplified ER diagram:

```
+--------+       +-----------+       +------------+
| Users  |------>| Items     |<------| Categories |
+--------+       +-----------+       +------------+
    |                 |                     ^
    |                 |                     |
    v                 v                     |
+---------------------|-----+               |
| Transactions        |     |---------------+
+----------------------+
```

- A one-to-many relationship exists between Users and Items (one user can sell many items)
- A one-to-many relationship exists between Categories and Items (one category can contain many items)
- A self-referential relationship exists between Categories (categories can have parent-child relationships)
- A many-to-many relationship exists between Users and Items via Transactions (users can buy many items, and items can be bought by one user)

### Database Schema

#### Users Table

The `users` table stores information about registered users:

```sql
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    password_hash VARCHAR(255)
);
```

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| user_id | INT | Unique identifier for each user | PRIMARY KEY, AUTO_INCREMENT |
| username | VARCHAR(100) | User's display name | NOT NULL |
| email | VARCHAR(255) | User's email address | Optional |
| phone | VARCHAR(50) | User's phone number | Optional |
| password_hash | VARCHAR(255) | Hashed user password | Optional (for future auth implementation) |

#### Categories Table

The `categories` table stores information about listed categories:

```sql
CREATE TABLE categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    parent_category_id INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_category_id) REFERENCES categories(category_id)
);
```

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| category_id | INT | Unique identifier for each category | PRIMARY KEY, AUTO_INCREMENT |
| name | VARCHAR(100) | Category name | NOT NULL |
| description | TEXT | Category description | Optional |
| parent_category_id | INT | Reference to parent category | FOREIGN KEY, Optional |
| created_at | DATETIME | When the category was created | DEFAULT CURRENT_TIMESTAMP |

#### Items Table

The `items` table stores information about listed items:

```sql
CREATE TABLE items (
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
```

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| item_id | INT | Unique identifier for each item | PRIMARY KEY, AUTO_INCREMENT |
| title | VARCHAR(255) | Item title/name | NOT NULL |
| description | TEXT | Detailed item description | Optional |
| price | DECIMAL(10, 2) | Item price with 2 decimal places | Optional |
| condition_status | VARCHAR(50) | Item condition (New, Used, etc.) | Optional |
| created_at | DATETIME | When the item was listed | DEFAULT CURRENT_TIMESTAMP |
| status | VARCHAR(50) | Current status (Available, Pending, Sold) | DEFAULT 'Available' |
| seller_id | INT | Reference to the user selling the item | FOREIGN KEY |
| category_id | INT | Reference to the item's category | FOREIGN KEY |
| contact_preference | VARCHAR(50) | Seller's preferred contact method | Optional |
| location | VARCHAR(255) | Item pickup/sale location | Optional |
| image_data | LONGBLOB | Binary data for item image | Optional |

#### Transactions Table

The `transactions` table stores information about completed transactions:

```sql
CREATE TABLE transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    item_id INT NOT NULL,
    seller_id INT NOT NULL,
    buyer_id INT NOT NULL,
    transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    price DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'Completed',
    payment_method VARCHAR(50),
    notes TEXT
);
```

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| transaction_id | INT | Unique identifier for each transaction | PRIMARY KEY, AUTO_INCREMENT |
| item_id | INT | Reference to the purchased item | FOREIGN KEY, NOT NULL |
| seller_id | INT | Reference to the item seller | FOREIGN KEY, NOT NULL |
| buyer_id | INT | Reference to the item buyer | FOREIGN KEY, NOT NULL |
| transaction_date | DATETIME | When the transaction occurred | DEFAULT CURRENT_TIMESTAMP |
| price | DECIMAL(10, 2) | Final transaction price | NOT NULL |
| status | VARCHAR(50) | Transaction status | DEFAULT 'Completed' |
| payment_method | VARCHAR(50) | Method of payment | Optional |
| notes | TEXT | Additional transaction notes | Optional |

### Normalization

The database schema follows these normalization principles:

1. **First Normal Form (1NF)**:
   - All tables have a primary key
   - Each column contains atomic values
   - No repeating groups

2. **Second Normal Form (2NF)**:
   - All non-key attributes are fully dependent on the primary key
   - No partial dependencies exist

3. **Third Normal Form (3NF)**:
   - No transitive dependencies
   - All non-key attributes depend directly on the primary key, not on other non-key attributes

4. **Boyce-Codd Normal Form (BCNF)**:
   - Every determinant is a candidate key
   - The categories hierarchy is properly modeled using a self-referential relationship

### Relationships

The database implements the following relationships:

1. **One-to-Many: Users to Items**
   - One user can sell many items
   - Each item has exactly one seller
   - Implemented via the `seller_id` foreign key in the `items` table
   - Ensures referential integrity (an item can't exist without a valid seller)

2. **One-to-Many: Categories to Items**
   - One category can contain many items
   - Each item belongs to exactly one category
   - Implemented via the `category_id` foreign key in the `items` table
   - Enables proper classification and filtering of marketplace items

3. **Self-Referential Relationship: Categories to Subcategories**
   - Categories can have parent-child relationships
   - Implemented via the `parent_category_id` foreign key in the `categories` table
   - Enables hierarchical organization of product categories

4. **Many-to-Many: Users to Items via Transactions**
   - Users can buy many items, and items can be bought by one user
   - Implemented via the `transactions` table with `seller_id`, `buyer_id` and `item_id` foreign keys
   - Records the history of completed purchases in the marketplace

### Schema Evolution

The application includes a schema evolution mechanism (`check_and_update_schema()`) that:

1. Checks for missing columns in existing tables
2. Adds new columns when necessary without data loss
3. Maintains backward compatibility as the application evolves
4. Automatically creates a default user if one doesn't exist

This approach allows for non-destructive database schema updates, demonstrating the concept of schema migration in a real application.

## 💻 Implementation

### Database Connection and Initialization

```python
def get_connection():
    """Return a connection to the MySQL database."""
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password='your_password',
        database=DB_NAME
    )

def init_db():
    """Initializes the database and tables if they do not exist."""
    # Implementation details...
```

### ORM Models

```python
from sqlalchemy.orm import sessionmaker, relationship, backref

class User(Base):
    """ORM model for the users table"""
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    password_hash = Column(String(255))
    
    # Relationship to items (one-to-many)
    items = relationship("Item", back_populates="seller")
```

### Stored Procedures

```sql
CREATE PROCEDURE get_marketplace_stats(IN start_date_param VARCHAR(20), IN end_date_param VARCHAR(20))
BEGIN
    SELECT 
        COUNT(*) AS total_items,
        SUM(CASE WHEN status = 'Available' THEN 1 ELSE 0 END) AS available_items,
        SUM(CASE WHEN status = 'Sold' THEN 1 ELSE 0 END) AS sold_items,
        SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END) AS pending_items,
        AVG(price) AS avg_price,
        MIN(price) AS min_price,
        MAX(price) AS max_price,
        COUNT(DISTINCT seller_id) AS total_sellers
    FROM items
    WHERE created_at BETWEEN start_date_param AND CONCAT(end_date_param, ' 23:59:59');
END
```

## 🔍 Query Examples

The application utilizes various SQL queries for different features:

### Simple Selection Query

```sql
-- Get all available items
SELECT * FROM items WHERE status = 'Available' ORDER BY created_at DESC;
```

### Filtering with Multiple Conditions

```sql
-- Filter items by category, price range, and condition
SELECT * FROM items 
WHERE category = 'Electronics' 
  AND price BETWEEN 10 AND 50
  AND condition_status = 'Used - Like New';
```

### Aggregation Queries

```sql
-- Get category statistics
SELECT 
    category, 
    COUNT(*) AS item_count,
    AVG(price) AS avg_price,
    SUM(CASE WHEN status = 'Sold' THEN 1 ELSE 0 END) AS sold_count
FROM items
WHERE category IS NOT NULL
GROUP BY category
ORDER BY item_count DESC;
```

### Joins

```sql
-- Get items with seller information
SELECT i.*, u.username, u.email 
FROM items i 
LEFT JOIN users u ON i.seller_id = u.user_id 
WHERE i.status = 'Available';
```

### Case Statements

```sql
-- Categorize items by price range
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
```

### ORM Example

```python
# Create a new Item using ORM
new_item = Item(
    title=title,
    description=description,
    price=Decimal(price),
    condition_status=condition_status,
    seller_id=seller_id,
    category_id=category_id,
    contact_preference=contact_preference,
    location=location,
    created_at=datetime.now(),
    image_data=image_data
)

session.add(new_item)
session.commit()
```

## 🚀 Setup and Installation

1. Clone this repository
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Make sure you have MySQL installed and running
4. Update database connection settings in `database/db_setup.py` if needed
5. Run the application:
   ```
   streamlit run main.py
   ```

## 🔧 Technology Stack

- **Frontend**: Streamlit (Python web framework)
- **Database**: MySQL
- **Programming Language**: Python
- **Data Visualization**: Matplotlib, Pandas
- **Image Processing**: Pillow
- **ORM**: SQLAlchemy
- **Database Driver**: mysql-connector-python

## 📁 Project Structure

```
secondhand_market/
├── .streamlit/        # Streamlit configuration
├── database/          # Database setup and connection
│   ├── __init__.py
│   ├── db_setup.py    # Database initialization and schema management
│   ├── orm_models.py  # SQLAlchemy ORM models
│   └── create_procedures.py # Stored procedures definitions
├── pages/             # Individual application pages
│   ├── 1_Create_Item.py
│   ├── 2_View_Items.py
│   └── 3_Reports.py
├── main.py            # Main application entry point (Home page)
├── insert_sample_data.py # Script to add sample data
├── requirements.txt   # Python dependencies
└── README.md          # Project documentation
```

## 🔮 Future Enhancements

- User authentication system
- Messaging between buyers and sellers
- Transaction history
- Ratings and reviews
- Advanced search capabilities
- Mobile application

---

This project was developed for a Database Systems course to demonstrate practical applications of database concepts and design principles.

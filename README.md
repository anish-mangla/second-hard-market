# SecondHand Market Application

A comprehensive web-based marketplace platform that enables users to buy and sell secondhand items. This project was developed as a database systems course project to demonstrate various database concepts and implementations.

![SecondHand Market](https://cdn-icons-png.flaticon.com/512/3900/3900101.png)

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
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

## 💾 Database Design

### Entity Relationship Diagram

The database design follows this simplified ER diagram:

```
+-------+       +--------+
| USERS |---<---| ITEMS  |
+-------+       +--------+
```

- A one-to-many relationship exists between Users and Items (one user can sell many items)

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
    category VARCHAR(100),
    contact_preference VARCHAR(50),
    location VARCHAR(255),
    image_data LONGBLOB,
    FOREIGN KEY (seller_id) REFERENCES users(user_id)
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
| category | VARCHAR(100) | Item category | Optional |
| contact_preference | VARCHAR(50) | Seller's preferred contact method | Optional |
| location | VARCHAR(255) | Item pickup/sale location | Optional |
| image_data | LONGBLOB | Binary data for item image | Optional |

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

### Relationships

The database implements the following relationships:

1. **One-to-Many: Users to Items**
   - One user can sell many items
   - Each item has exactly one seller
   - Implemented via the `seller_id` foreign key in the `items` table
   - Ensures referential integrity (an item can't exist without a valid seller)

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

## 📁 Project Structure

```
secondhand_market/
├── .streamlit/        # Streamlit configuration
├── database/          # Database setup and connection
│   ├── __init__.py
│   └── db_setup.py    # Database initialization and schema management
├── pages/             # Individual application pages
│   ├── 1_Create_Item.py
│   ├── 2_View_Items.py
│   └── 3_Reports.py
├── main.py            # Main application entry point (Home page)
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

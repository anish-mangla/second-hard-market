"""
This script creates stored procedures for our database.
"""
from database.db_setup import get_connection

def create_procedures():
    """Create stored procedures in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Drop existing procedures before recreating
    cursor.execute("DROP PROCEDURE IF EXISTS get_marketplace_stats")
    cursor.execute("DROP PROCEDURE IF EXISTS category_analysis")
    cursor.execute("DROP PROCEDURE IF EXISTS price_distribution")
    cursor.execute("DROP PROCEDURE IF EXISTS get_items_by_filter")
    cursor.execute("DROP PROCEDURE IF EXISTS get_transaction_history")
    
    # Create procedure for marketplace statistics
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
    
    # Create procedure for category analysis
    cursor.execute("""
    CREATE PROCEDURE category_analysis(IN start_date_param VARCHAR(20), IN end_date_param VARCHAR(20))
    BEGIN
        SELECT 
            COALESCE(c.name, 'Uncategorized') AS category,
            COUNT(i.item_id) AS item_count,
            ROUND(AVG(i.price), 2) AS avg_price,
            SUM(CASE WHEN i.status = 'Sold' THEN 1 ELSE 0 END) AS sold_count
        FROM items i
        LEFT JOIN categories c ON i.category_id = c.category_id
        WHERE (start_date_param IS NULL OR i.created_at >= start_date_param)
        AND (end_date_param IS NULL OR i.created_at <= end_date_param)
        GROUP BY c.category_id
        ORDER BY item_count DESC;
    END
    """)
    
    # Create procedure for price distribution analysis
    cursor.execute("""
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
    """)
    
    # Create procedure to get items by filter (updated for category_id)
    cursor.execute("""
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
    """)
    
    # Create new procedure for transaction history reporting
    cursor.execute("""
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
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("Stored procedures created successfully!")

if __name__ == "__main__":
    create_procedures() 
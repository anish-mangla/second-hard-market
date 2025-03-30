"""
This script creates stored procedures for our database.
"""
from database.db_setup import get_connection

def create_procedures():
    """Create stored procedures in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Drop procedures if they exist to avoid errors
    cursor.execute("DROP PROCEDURE IF EXISTS get_marketplace_stats")
    cursor.execute("DROP PROCEDURE IF EXISTS get_category_analysis")
    cursor.execute("DROP PROCEDURE IF EXISTS get_price_distribution")
    
    # Create procedure for marketplace stats
    cursor.execute("""
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
    """)
    
    # Create procedure for category analysis
    cursor.execute("""
    CREATE PROCEDURE get_category_analysis()
    BEGIN
        SELECT 
            category, 
            COUNT(*) AS item_count,
            AVG(price) AS avg_price,
            SUM(CASE WHEN status = 'Sold' THEN 1 ELSE 0 END) AS sold_count
        FROM items
        WHERE category IS NOT NULL
        GROUP BY category
        ORDER BY item_count DESC;
    END
    """)
    
    # Create procedure for price distribution
    cursor.execute("""
    CREATE PROCEDURE get_price_distribution()
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
        GROUP BY price_range
        ORDER BY 
            CASE
                WHEN price_range = '$0-$10' THEN 1
                WHEN price_range = '$10-$25' THEN 2
                WHEN price_range = '$25-$50' THEN 3
                WHEN price_range = '$50-$100' THEN 4
                WHEN price_range = '$100-$250' THEN 5
                WHEN price_range = '$250-$500' THEN 6
                WHEN price_range = '$500+' THEN 7
                ELSE 8
            END;
    END
    """)
    
    # Drop procedures if they exist to avoid errors
    cursor.execute("DROP PROCEDURE IF EXISTS get_items_by_filter")
    
    # Create procedure to get items by dynamic filters
    cursor.execute("""
    CREATE PROCEDURE get_items_by_filter(
        IN category_param VARCHAR(100),
        IN min_price_param DECIMAL(10, 2),
        IN max_price_param DECIMAL(10, 2),
        IN condition_param VARCHAR(50),
        IN status_param VARCHAR(50)
    )
    BEGIN
        SELECT i.*, u.username, u.email 
        FROM items i 
        LEFT JOIN users u ON i.seller_id = u.user_id 
        WHERE 1=1
            AND (category_param IS NULL OR category_param = '' OR i.category = category_param)
            AND (i.price BETWEEN min_price_param AND max_price_param)
            AND (condition_param IS NULL OR condition_param = '' OR condition_param = 'All Conditions' OR i.condition_status = condition_param)
            AND (status_param IS NULL OR status_param = '' OR i.status = status_param)
        ORDER BY i.created_at DESC;
    END
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("Stored procedures created successfully!")

if __name__ == "__main__":
    create_procedures() 
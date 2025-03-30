# secondhand_market/pages/3_Reports.py

import streamlit as st
from database.db_setup import get_connection
import pandas as pd
import matplotlib.pyplot as plt
import io
from datetime import datetime, timedelta
import calendar
import decimal
from database.transaction_manager import transaction, IsolationLevel

# Helper function to convert Decimal to int/float
def convert_decimal(value):
    if isinstance(value, decimal.Decimal):
        return int(value) if value % 1 == 0 else float(value)
    return value

def reports_page():
    st.title("Marketplace Reports & Analytics")
    st.write("Get insights into marketplace activity and item statistics.")
    
    # Check if stored procedures need to be created
    st.info("This page uses stored procedures to generate reports efficiently.")
    
    # Ensure stored procedures exist
    from database.create_procedures import create_procedures
    create_procedures()
    
    # Create tabs for different report types
    tab1, tab2, tab3 = st.tabs(["Overview", "Category Analysis", "Price & Condition Analysis"])
    
    with tab1:
        display_overview_stats()
    
    with tab2:
        display_category_analysis()
    
    with tab3:
        display_price_condition_analysis()

def display_overview_stats():
    """Display overview statistics about the marketplace using stored procedure"""
    st.header("Marketplace Overview")
    
    # Date range selector for the overview
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("From date", value=datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("To date", value=datetime.now())
    
    # Convert dates to strings for SQL query
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    # Get basic stats using stored procedure
    con = get_connection()
    cur = con.cursor(dictionary=True)
    
    # Call the stored procedure
    cur.execute("CALL get_marketplace_stats(%s, %s)", (start_date_str, end_date_str))
    stats_raw = cur.fetchone()
    
    # Need to fetch from next result set (if any)
    if cur.nextset():
        pass
    
    # Convert all Decimal values to int/float
    stats = {k: convert_decimal(v) for k, v in stats_raw.items()}
    
    # Display metrics in a grid
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    with metric_col1:
        st.metric("Total Items", stats["total_items"])
    with metric_col2:
        st.metric("Available Items", stats["available_items"])
    with metric_col3:
        st.metric("Sold Items", stats["sold_items"])
    with metric_col4:
        st.metric("Pending Items", stats["pending_items"])
    
    # Second row of metrics
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    with metric_col1:
        avg_price = stats['avg_price']
        st.metric("Average Price", f"${avg_price:.2f}" if avg_price is not None else "$0.00")
    with metric_col2:
        min_price = stats['min_price']
        st.metric("Min Price", f"${min_price:.2f}" if min_price is not None else "$0.00")
    with metric_col3:
        max_price = stats['max_price']
        st.metric("Max Price", f"${max_price:.2f}" if max_price is not None else "$0.00")
    with metric_col4:
        st.metric("Total Sellers", stats["total_sellers"])
    
    # Get weekly items added - using prepared statement for this one
    weekly_query = f"""
        SELECT 
            DATE_FORMAT(created_at, '%Y-%m-%d') AS date,
            COUNT(*) AS num_items
        FROM items
        WHERE created_at BETWEEN %s AND %s
        GROUP BY DATE_FORMAT(created_at, '%Y-%m-%d')
        ORDER BY date
    """
    
    cur.execute(weekly_query, (start_date_str, end_date_str + " 23:59:59"))
    weekly_results_raw = cur.fetchall()
    cur.close()
    con.close()
    
    # Convert to DataFrame for easier plotting
    if weekly_results_raw:
        # Convert any Decimal values in the results
        weekly_results = []
        for row in weekly_results_raw:
            weekly_results.append({k: convert_decimal(v) for k, v in row.items()})
            
        weekly_df = pd.DataFrame(weekly_results)
        
        # Plot weekly items added
        st.subheader("Items Added per Day")
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar(weekly_df['date'], weekly_df['num_items'], color='#1f77b4')
        ax.set_xlabel('Date')
        ax.set_ylabel('Number of Items')
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.info("No data available for the selected date range.")

def display_category_analysis():
    """Display category-based analysis using stored procedure"""
    st.header("Category Analysis")
    
    # Get category distribution using stored procedure
    con = get_connection()
    cur = con.cursor(dictionary=True)
    
    # Call the stored procedure
    cur.execute("CALL get_category_analysis()")
    category_results_raw = cur.fetchall()
    cur.close()
    con.close()
    
    if category_results_raw:
        # Convert any Decimal values in the results
        category_results = []
        for row in category_results_raw:
            category_results.append({k: convert_decimal(v) for k, v in row.items()})
            
        # Convert to DataFrame
        category_df = pd.DataFrame(category_results)
        
        # Calculate sell-through rate
        category_df['sell_through_rate'] = (category_df['sold_count'] / category_df['item_count'] * 100).round(1)
        
        # Display as a bar chart
        st.subheader("Items by Category")
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.barh(category_df['category'], category_df['item_count'], color='#2ca02c')
        ax.set_xlabel('Number of Items')
        ax.set_ylabel('Category')
        
        # Add count labels to the bars
        for i, v in enumerate(category_df['item_count']):
            ax.text(v + 0.1, i, str(v), va='center')
            
        plt.tight_layout()
        st.pyplot(fig)
        
        # Display average price by category
        st.subheader("Average Price by Category")
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.barh(category_df['category'], category_df['avg_price'], color='#d62728')
        ax.set_xlabel('Average Price ($)')
        ax.set_ylabel('Category')
        
        # Add price labels to the bars
        for i, v in enumerate(category_df['avg_price']):
            ax.text(v + 0.1, i, f"${v:.2f}", va='center')
            
        plt.tight_layout()
        st.pyplot(fig)
        
        # Display category data as a table
        st.subheader("Category Statistics")
        
        # Format the dataframe for display
        display_df = category_df.copy()
        display_df['avg_price'] = display_df['avg_price'].apply(lambda x: f"${x:.2f}")
        display_df['sell_through_rate'] = display_df['sell_through_rate'].apply(lambda x: f"{x}%")
        display_df.columns = ['Category', 'Total Items', 'Average Price', 'Sold Items', 'Sell-Through Rate']
        
        st.dataframe(display_df)
    else:
        st.info("No category data available.")

def display_price_condition_analysis():
    """Display price and condition analysis"""
    st.header("Price & Condition Analysis")
    
    # Get condition distribution using prepared statement 
    con = get_connection()
    cur = con.cursor(dictionary=True)
    
    condition_query = """
        SELECT 
            condition_status, 
            COUNT(*) AS item_count,
            AVG(price) AS avg_price
        FROM items
        WHERE condition_status IS NOT NULL
        GROUP BY condition_status
        ORDER BY 
            CASE 
                WHEN condition_status = 'New' THEN 1
                WHEN condition_status = 'Used - Like New' THEN 2
                WHEN condition_status = 'Used - Good' THEN 3
                WHEN condition_status = 'Used - Acceptable' THEN 4
                WHEN condition_status = 'For parts' THEN 5
                ELSE 6
            END
    """
    
    cur.execute(condition_query)
    condition_results_raw = cur.fetchall()
    
    # Get price distribution using stored procedure
    cur.execute("CALL get_price_distribution()")
    price_results_raw = cur.fetchall()
    cur.close()
    con.close()
    
    col1, col2 = st.columns(2)
    
    # Condition analysis
    with col1:
        if condition_results_raw:
            # Convert any Decimal values in the results
            condition_results = []
            for row in condition_results_raw:
                condition_results.append({k: convert_decimal(v) for k, v in row.items()})
                
            condition_df = pd.DataFrame(condition_results)
            
            st.subheader("Items by Condition")
            fig, ax = plt.subplots(figsize=(8, 5))
            plt.pie(condition_df['item_count'], labels=condition_df['condition_status'], autopct='%1.1f%%', startangle=90)
            plt.axis('equal')
            plt.tight_layout()
            st.pyplot(fig)
            
            # Table of condition data
            st.markdown("##### Condition Statistics")
            condition_display_df = condition_df.copy()
            condition_display_df['avg_price'] = condition_display_df['avg_price'].apply(lambda x: f"${x:.2f}")
            condition_display_df.columns = ['Condition', 'Count', 'Average Price']
            st.dataframe(condition_display_df)
    
    # Price range analysis
    with col2:
        if price_results_raw:
            # Convert any Decimal values in the results
            price_results = []
            for row in price_results_raw:
                price_results.append({k: convert_decimal(v) for k, v in row.items()})
                
            price_df = pd.DataFrame(price_results)
            
            st.subheader("Items by Price Range")
            fig, ax = plt.subplots(figsize=(8, 5))
            plt.pie(price_df['item_count'], labels=price_df['price_range'], autopct='%1.1f%%', startangle=90)
            plt.axis('equal')
            plt.tight_layout()
            st.pyplot(fig)
            
            # Table of price range data
            st.markdown("##### Price Range Distribution")
            price_df.columns = ['Price Range', 'Count']
            st.dataframe(price_df)

def show_marketplace_stats(start_date=None, end_date=None):
    """Show overall marketplace statistics"""
    try:
        # Use READ COMMITTED isolation for reports - balance between consistency and performance
        with transaction(IsolationLevel.READ_COMMITTED) as (conn, cursor):
            st.write("Using transactions with READ COMMITTED isolation level for report generation")
            
            cursor.execute("CALL get_marketplace_stats(%s, %s)", [start_date, end_date])
            stats = cursor.fetchone()
            
            if stats:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Items", int(stats["total_items"]))
                
                with col2:
                    st.metric("Available Items", int(stats["available_count"]))
                
                with col3:
                    st.metric("Sold Items", int(stats["sold_count"]))
                
                with col4:
                    st.metric("Average Price", f"${float(stats['avg_price']):.2f}")
    except Exception as e:
        st.error(f"Error generating marketplace stats: {str(e)}")

def show_category_analysis(start_date=None, end_date=None):
    """Show analysis by category"""
    try:
        # Use READ COMMITTED for category analysis
        with transaction(IsolationLevel.READ_COMMITTED) as (conn, cursor):
            cursor.execute("CALL category_analysis(%s, %s)", [start_date, end_date])
            category_data = cursor.fetchall()
            
            if category_data:
                # Display as a bar chart and a table
                category_counts = {row['category'] if row['category'] else 'Uncategorized': row['item_count'] 
                                for row in category_data}
                
                # ... rest of the display code remains unchanged ...
    except Exception as e:
        st.error(f"Error generating category analysis: {str(e)}")

def show_complex_statistics():
    """Show more complex statistics that benefit from SERIALIZABLE isolation"""
    try:
        # Use SERIALIZABLE for complex reports that need to be consistent
        with transaction(IsolationLevel.SERIALIZABLE) as (conn, cursor):
            st.write("Using SERIALIZABLE isolation for complex statistical analysis")
            
            # Get average items per seller
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT seller_id) as seller_count,
                    COUNT(*) as item_count,
                    ROUND(COUNT(*) / COUNT(DISTINCT seller_id), 2) as avg_items_per_seller
                FROM items
            """)
            seller_stats = cursor.fetchone()
            
            # Get price distribution
            cursor.execute("CALL price_distribution()")
            price_data = cursor.fetchall()
            
            # Display the seller statistics
            if seller_stats:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Sellers", int(seller_stats["seller_count"]))
                with col2:
                    st.metric("Total Items", int(seller_stats["item_count"]))
                with col3:
                    st.metric("Avg Items/Seller", float(seller_stats["avg_items_per_seller"]))
                
            # Display price distribution
            if price_data:
                # ... display code for price distribution ...
                price_ranges = [row['price_range'] for row in price_data]
                item_counts = [row['item_count'] for row in price_data]
                
                # Create a DataFrame for the chart
                df = pd.DataFrame({
                    'Price Range': price_ranges,
                    'Item Count': item_counts
                })
                
                # Create a bar chart
                fig, ax = plt.subplots(figsize=(10, 6))
                bars = ax.bar(price_ranges, item_counts, color='skyblue')
                ax.set_xlabel('Price Range')
                ax.set_ylabel('Number of Items')
                ax.set_title('Price Distribution of Items')
                ax.tick_params(axis='x', rotation=45)
                
                # Add the count on top of each bar
                for bar in bars:
                    height = bar.get_height()
                    ax.annotate(f'{height}',
                                xy=(bar.get_x() + bar.get_width() / 2, height),
                                xytext=(0, 3),  # 3 points vertical offset
                                textcoords="offset points",
                                ha='center', va='bottom')
                
                plt.tight_layout()
                st.pyplot(fig)
                
                # Also show as a table
                st.dataframe(df)
    except Exception as e:
        st.error(f"Error generating complex statistics: {str(e)}")

def app():
    reports_page()

if __name__ == "__main__":
    app()

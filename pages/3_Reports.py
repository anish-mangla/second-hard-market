# secondhand_market/pages/3_Reports.py

import streamlit as st
from database.db_setup import get_connection
import pandas as pd
import matplotlib.pyplot as plt
import io
from datetime import datetime, timedelta
import calendar
import decimal
import numpy as np
from database.transaction_manager import transaction, IsolationLevel
from database.create_procedures import create_procedures
from database.orm_models import get_session, Transaction, Item, User, Category

# Helper function to convert Decimal to int/float
def convert_decimal(value):
    if isinstance(value, decimal.Decimal):
        return int(value) if value % 1 == 0 else float(value)
    return value

def reports_page():
    """Display various marketplace reports and analytics"""
    st.title("Marketplace Reports")
    
    # Ensure stored procedures exist
    create_procedures()
    
    # Date range selector for filtering reports
    st.sidebar.header("Report Filters")
    
    # Choose report period
    report_period = st.sidebar.selectbox(
        "Report Period",
        ["Last 7 days", "Last 30 days", "Last 90 days", "All time", "Custom"]
    )
    
    # Calculate date range based on selection
    today = datetime.now().date()
    
    if report_period == "Last 7 days":
        start_date = today - timedelta(days=7)
        end_date = today
    elif report_period == "Last 30 days":
        start_date = today - timedelta(days=30)
        end_date = today
    elif report_period == "Last 90 days":
        start_date = today - timedelta(days=90)
        end_date = today
    elif report_period == "All time":
        start_date = None
        end_date = None
    else:  # Custom
        col1, col2 = st.sidebar.columns(2)
        with col1:
            start_date = st.date_input("From", value=today - timedelta(days=30), key="sidebar_start")
        with col2:
            end_date = st.date_input("To", value=today, key="sidebar_end")
    
    # Format dates for MySQL
    start_date_str = start_date.strftime('%Y-%m-%d') if start_date else None
    end_date_str = end_date.strftime('%Y-%m-%d') if end_date else None
    
    # Display appropriate date range in the header with styling
    if start_date and end_date:
        st.markdown(f"### 📊 Market Analytics: {start_date.strftime('%b %d, %Y')} - {end_date.strftime('%b %d, %Y')}")
    else:
        st.markdown("### 📊 Market Analytics: All Time")
    
    st.markdown("---")
    
    # Create tabs for different report types
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📈 Marketplace Overview", 
        "🔍 Category Analysis", 
        "💰 Price Distribution",
        "🛒 Transaction History",
        "📅 Seasonal Trends",
        "👥 User Activity"
    ])
    
    with tab1:
        show_marketplace_stats(start_date_str, end_date_str)
    
    with tab2:
        show_category_analysis(start_date_str, end_date_str)
    
    with tab3:
        show_price_distribution()
        show_condition_price_analysis()
        
    with tab4:
        show_transaction_history()
        
    with tab5:
        show_seasonal_trends()
        
    with tab6:
        show_user_activity()

def show_marketplace_stats(start_date=None, end_date=None):
    """Show overall marketplace statistics"""
    try:
        with transaction(IsolationLevel.READ_COMMITTED) as (conn, cursor):
            cursor.execute("CALL get_marketplace_stats(%s, %s)", [start_date, end_date])
            stats = cursor.fetchone()
            
            # Process the results...
    except Exception as e:
        st.error(f"Error generating marketplace stats: {str(e)}")

def show_category_analysis(start_date=None, end_date=None):
    """Show analysis by category"""
    try:
        # Use READ COMMITTED for category analysis
        with transaction(IsolationLevel.READ_COMMITTED) as (conn, cursor):
            # First check if there are any items at all
            cursor.execute("SELECT COUNT(*) as item_count FROM items")
            item_count = cursor.fetchone()['item_count']
            
            if item_count == 0:
                st.info("No items in the database yet. Add some items to see category analysis.")
                return
            
            # Then proceed with category analysis
            cursor.execute("CALL category_analysis(%s, %s)", [start_date, end_date])
            category_data = cursor.fetchall()
            
            # Make sure to consume any additional result sets
            while cursor.nextset():
                pass
            
            if category_data:
                # Create a DataFrame for easier visualization
                df = pd.DataFrame(category_data)
                
                st.markdown("### Category Distribution")
                # Display as a bar chart 
                fig, ax = plt.subplots(figsize=(10, 6))
                categories = [row['category'] or 'Uncategorized' for row in category_data]
                # Ensure item_count values are not None
                item_counts = [row['item_count'] if row['item_count'] is not None else 0 for row in category_data]
                
                # Use a more attractive color palette
                colors = plt.cm.Greens(np.linspace(0.5, 0.9, len(categories)))
                bars = ax.bar(categories, item_counts, color=colors)
                
                # Add count labels on top of each bar
                for bar in bars:
                    height = bar.get_height()
                    ax.annotate(f'{height}',
                                xy=(bar.get_x() + bar.get_width()/2, height),
                                xytext=(0, 3),  # 3 points vertical offset
                                textcoords="offset points",
                                ha='center', va='bottom')
                
                ax.set_xlabel('Category')
                ax.set_ylabel('Number of Items')
                ax.set_title('Items by Category')
                ax.tick_params(axis='x', rotation=45)
                plt.tight_layout()
                
                st.pyplot(fig)
                
                # Try to add a pie chart if there are not too many categories
                if len(categories) <= 10:
                    st.markdown("### Category Proportions")
                    fig, ax = plt.subplots(figsize=(8, 8))
                    ax.pie(item_counts, labels=categories, autopct='%1.1f%%', 
                           startangle=90, shadow=True, 
                           colors=plt.cm.Paired(np.linspace(0, 1, len(categories))))
                    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
                    plt.title("Category Distribution", fontsize=16)
                    st.pyplot(fig)
                
                # Display detailed metrics as a table
                st.markdown("### Category Details")
                display_df = df.copy()
                # Handle None values in avg_price
                display_df['avg_price'] = display_df['avg_price'].apply(lambda x: f"${float(x if x is not None else 0):.2f}")
                display_df = display_df.rename(columns={
                    'category': 'Category',
                    'item_count': 'Total Items',
                    'avg_price': 'Average Price',
                    'sold_count': 'Sold Items'
                })
                st.dataframe(display_df, use_container_width=True)
            else:
                st.info("No category data available to analyze.")
    except Exception as e:
        st.error(f"Error generating category analysis: {str(e)}")

def show_price_distribution():
    """Show price distribution of items"""
    st.markdown("### 💲 Price Distribution")
    
    try:
        # Use READ COMMITTED isolation for reports
        with transaction(IsolationLevel.READ_COMMITTED) as (conn, cursor):
            # Call the stored procedure for price distribution
            cursor.execute("CALL price_distribution()")
            price_data = cursor.fetchall()
            
            # Make sure to consume any additional result sets
            while cursor.nextset():
                pass
            
            if not price_data:
                st.info("No price data available to analyze.")
                return
                
            # Create a pandas DataFrame for the visualization
            price_ranges = [row['price_range'] for row in price_data]
            # Ensure item_count values are not None
            item_counts = [row['item_count'] if row['item_count'] is not None else 0 for row in price_data]
            
            df = pd.DataFrame({
                'Price Range': price_ranges,
                'Item Count': item_counts
            })
            
            # Create and display the bar chart
            fig, ax = plt.subplots(figsize=(10, 6))
            colors = plt.cm.Blues(np.linspace(0.5, 0.9, len(price_ranges)))
            bars = ax.bar(price_ranges, item_counts, color=colors)
            
            # Add count labels on top of each bar
            for bar in bars:
                height = bar.get_height()
                ax.annotate(f'{height}',
                            xy=(bar.get_x() + bar.get_width()/2, height),
                            xytext=(0, 3),  # 3 points vertical offset
                            textcoords="offset points",
                            ha='center', va='bottom')
            
            ax.set_xlabel('Price Range')
            ax.set_ylabel('Number of Items')
            ax.set_title('Price Distribution of Items')
            ax.tick_params(axis='x', rotation=45)
            plt.tight_layout()
            
            st.pyplot(fig)
            
            # Also display as a table
            st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"Error generating price distribution: {str(e)}")

def show_condition_price_analysis():
    """Show relationship between item condition and price"""
    st.markdown("### 👍 Price by Condition Analysis")
    
    try:
        with transaction(IsolationLevel.READ_COMMITTED) as (conn, cursor):
            # Get price data by condition
            cursor.execute("""
                SELECT 
                    condition_status,
                    ROUND(AVG(price), 2) as avg_price,
                    MIN(price) as min_price,
                    MAX(price) as max_price,
                    COUNT(*) as item_count
                FROM items
                GROUP BY condition_status
                ORDER BY 
                    CASE 
                        WHEN condition_status = 'New' THEN 1
                        WHEN condition_status = 'Like New' THEN 2
                        WHEN condition_status = 'Good' THEN 3
                        WHEN condition_status = 'Fair' THEN 4
                        WHEN condition_status = 'Poor' THEN 5
                        ELSE 6
                    END
            """)
            
            condition_data = cursor.fetchall()
            while cursor.nextset():
                pass
                
            if condition_data:
                # Create DataFrame
                condition_df = pd.DataFrame(condition_data)
                
                # Display condition data as a table
                st.markdown("#### Condition Price Summary")
                display_df = condition_df.copy()
                # Handle None values in price columns
                display_df['avg_price'] = display_df['avg_price'].apply(lambda x: f"${float(x if x is not None else 0):.2f}")
                display_df['min_price'] = display_df['min_price'].apply(lambda x: f"${float(x if x is not None else 0):.2f}")
                display_df['max_price'] = display_df['max_price'].apply(lambda x: f"${float(x if x is not None else 0):.2f}")
                
                display_df = display_df.rename(columns={
                    'condition_status': 'Condition',
                    'avg_price': 'Average Price',
                    'min_price': 'Minimum Price',
                    'max_price': 'Maximum Price',
                    'item_count': 'Item Count'
                })
                
                st.dataframe(display_df, use_container_width=True)
                
                # Create a bar chart of average prices by condition
                fig, ax = plt.subplots(figsize=(10, 6))
                conditions = [row['condition_status'] for row in condition_data]
                # Handle None values in avg_price
                avg_prices = [float(row['avg_price'] if row['avg_price'] is not None else 0) for row in condition_data]
                
                # Use a color gradient based on condition (green for new, yellow for good, etc)
                condition_colors = {
                    'New': '#2ecc71',       # Green
                    'Like New': '#27ae60',  # Darker green
                    'Good': '#f1c40f',      # Yellow
                    'Fair': '#e67e22',      # Orange
                    'Poor': '#e74c3c'       # Red
                }
                
                colors = [condition_colors.get(condition, '#3498db') for condition in conditions]
                bars = ax.bar(conditions, avg_prices, color=colors)
                
                # Add average price labels on top of each bar
                for bar in bars:
                    height = bar.get_height()
                    ax.annotate(f'${height:.2f}',
                                xy=(bar.get_x() + bar.get_width()/2, height),
                                xytext=(0, 3),  # 3 points vertical offset
                                textcoords="offset points",
                                ha='center', va='bottom')
                
                ax.set_xlabel('Condition')
                ax.set_ylabel('Average Price ($)')
                ax.set_title('Average Price by Item Condition')
                ax.grid(axis='y', linestyle='--', alpha=0.7)
                
                st.pyplot(fig)
            else:
                st.info("No condition data available to analyze.")
    except Exception as e:
        st.error(f"Error generating condition price analysis: {str(e)}")

def show_seasonal_trends():
    """Show seasonal trends in the marketplace"""
    st.markdown("### 📅 Seasonal Marketplace Trends")
    
    try:
        with transaction(IsolationLevel.READ_COMMITTED) as (conn, cursor):
            # Get monthly item count data
            cursor.execute("""
                SELECT 
                    DATE_FORMAT(created_at, '%Y-%m') as month,
                    COUNT(*) as item_count,
                    ROUND(AVG(price), 2) as avg_price,
                    SUM(CASE WHEN status = 'Sold' THEN 1 ELSE 0 END) as sold_count
                FROM items
                WHERE created_at >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
                GROUP BY DATE_FORMAT(created_at, '%Y-%m')
                ORDER BY month
            """)
            
            monthly_data = cursor.fetchall()
            while cursor.nextset():
                pass
            
            if not monthly_data or len(monthly_data) < 2:
                st.info("Not enough data available for trend analysis. Need at least 2 months of data.")
                return
                
            # Create DataFrames for visualization
            months = [row['month'] for row in monthly_data]
            # Handle None values in metrics
            item_counts = [row['item_count'] if row['item_count'] is not None else 0 for row in monthly_data]
            avg_prices = [float(row['avg_price'] if row['avg_price'] is not None else 0) for row in monthly_data]
            sold_counts = [row['sold_count'] if row['sold_count'] is not None else 0 for row in monthly_data]
            
            # Format month labels for better display
            formatted_months = []
            for month_str in months:
                year, month = month_str.split('-')
                month_name = calendar.month_abbr[int(month)]
                formatted_months.append(f"{month_name} {year}")
            
            st.markdown("#### 📊 Monthly Listing & Sales Trends")
            # Create line chart for monthly listings and sales
            fig, ax1 = plt.subplots(figsize=(10, 6))
            
            color = '#3498db'  # Blue
            ax1.set_xlabel('Month')
            ax1.set_ylabel('Total Items', color=color)
            line1 = ax1.plot(formatted_months, item_counts, color=color, marker='o', label='New Listings', linewidth=3)
            ax1.tick_params(axis='y', labelcolor=color)
            ax1.tick_params(axis='x', rotation=45)
            ax1.grid(axis='y', linestyle='--', alpha=0.3)
            
            # Create second y-axis
            ax2 = ax1.twinx()
            color = '#2ecc71'  # Green
            ax2.set_ylabel('Sold Items', color=color)
            line2 = ax2.plot(formatted_months, sold_counts, color=color, marker='s', label='Sold Items', linewidth=3)
            ax2.tick_params(axis='y', labelcolor=color)
            
            # Combine legends
            lines = line1 + line2
            labels = [l.get_label() for l in lines]
            ax1.legend(lines, labels, loc='upper left')
            
            plt.title('Monthly Listing and Sales Trends')
            plt.tight_layout()
            st.pyplot(fig)
            
            st.markdown("#### 💰 Price Trend Analysis")
            # Create price trend chart
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(formatted_months, avg_prices, marker='o', color='#9b59b6', linewidth=3)  # Purple
            
            # Add price labels
            for i, price in enumerate(avg_prices):
                ax.annotate(f'${price:.2f}', 
                           (i, price),
                           textcoords="offset points",
                           xytext=(0,10), 
                           ha='center')
            
            ax.set_xlabel('Month')
            ax.set_ylabel('Average Price ($)')
            ax.set_title('Monthly Average Price Trend')
            ax.tick_params(axis='x', rotation=45)
            ax.grid(True, linestyle='--', alpha=0.7)
            
            plt.tight_layout()
            st.pyplot(fig)
    except Exception as e:
        st.error(f"Error generating seasonal trends: {str(e)}")

def show_user_activity():
    """Show user activity statistics"""
    st.markdown("### 👥 User Activity Analytics")
    
    try:
        with transaction(IsolationLevel.READ_COMMITTED) as (conn, cursor):
            # Get seller activity data
            cursor.execute("""
                SELECT 
                    u.username,
                    COUNT(i.item_id) as item_count,
                    SUM(CASE WHEN i.status = 'Sold' THEN 1 ELSE 0 END) as sold_count,
                    ROUND(AVG(i.price), 2) as avg_price,
                    MIN(i.created_at) as first_listing,
                    MAX(i.created_at) as last_listing
                FROM users u
                LEFT JOIN items i ON u.user_id = i.seller_id
                GROUP BY u.user_id
                HAVING item_count > 0
                ORDER BY item_count DESC
            """)
            
            seller_data = cursor.fetchall()
            while cursor.nextset():
                pass
                
            if seller_data:
                # Create DataFrame for visualization
                df_sellers = pd.DataFrame(seller_data)
                
                # Show top sellers
                st.markdown("#### 🏆 Top Sellers")
                
                # Create bar chart for top sellers
                fig, ax = plt.subplots(figsize=(10, 6))
                
                # Limit to top 10 sellers for visualization
                top_sellers = df_sellers.head(10) if len(df_sellers) > 10 else df_sellers
                
                usernames = [row['username'] for row in top_sellers.to_dict('records')]
                item_counts = [row['item_count'] for row in top_sellers.to_dict('records')]
                sold_counts = [row['sold_count'] for row in top_sellers.to_dict('records')]
                
                # Create grouped bar chart
                x = np.arange(len(usernames))
                width = 0.35
                
                ax.bar(x - width/2, item_counts, width, label='Listed Items', color='#3498db')  # Blue
                ax.bar(x + width/2, sold_counts, width, label='Sold Items', color='#2ecc71')  # Green
                
                ax.set_xlabel('Seller')
                ax.set_ylabel('Number of Items')
                ax.set_title('Top Sellers Activity')
                ax.set_xticks(x)
                ax.set_xticklabels(usernames, rotation=45, ha='right')
                ax.legend()
                ax.grid(axis='y', linestyle='--', alpha=0.3)
                
                plt.tight_layout()
                st.pyplot(fig)
                
                # Show seller stats table
                st.markdown("#### 📋 Seller Details")
                display_df = df_sellers.copy()
                display_df['avg_price'] = display_df['avg_price'].apply(lambda x: f"${float(x):.2f}")
                if 'first_listing' in display_df.columns and display_df['first_listing'].dtype != 'object':
                    display_df['first_listing'] = pd.to_datetime(display_df['first_listing']).dt.strftime('%Y-%m-%d')
                if 'last_listing' in display_df.columns and display_df['last_listing'].dtype != 'object':
                    display_df['last_listing'] = pd.to_datetime(display_df['last_listing']).dt.strftime('%Y-%m-%d')
                
                display_df = display_df.rename(columns={
                    'username': 'Seller',
                    'item_count': 'Total Listings',
                    'sold_count': 'Items Sold',
                    'avg_price': 'Average Price',
                    'first_listing': 'First Listing',
                    'last_listing': 'Last Listing'
                })
                
                st.dataframe(display_df, use_container_width=True)
                
                # Calculate sell-through rate
                st.markdown("#### 📈 Seller Performance Metrics")
                
                display_df['Sell-through Rate'] = (display_df['Items Sold'] / display_df['Total Listings'] * 100).apply(lambda x: f"{x:.1f}%")
                
                # Only show performance metrics
                performance_cols = ['Seller', 'Total Listings', 'Items Sold', 'Sell-through Rate', 'Average Price']
                st.dataframe(display_df[performance_cols], use_container_width=True)
            else:
                    st.info("No seller activity data available.")
    except Exception as e:
        st.error(f"Error generating user activity analytics: {str(e)}")

def show_transaction_history():
    """Show transaction history and analytics"""
    st.markdown("### 🛒 Transaction History")
    
    # Date range selector for transactions
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("From", value=datetime.now().date() - timedelta(days=30), key="trans_start_date")
    with col2:
        end_date = st.date_input("To", value=datetime.now().date(), key="trans_end_date")
    
    # User filter (seller or buyer)
    filter_type = st.radio("Filter by:", ["All Transactions", "As Seller", "As Buyer"], horizontal=True)
    
    seller_id = None
    buyer_id = None
    
    if filter_type == "As Seller":
        seller_id = 1  # Default user ID, in a real app this would be the current user
    elif filter_type == "As Buyer":
        buyer_id = 1   # Default user ID, in a real app this would be the current user
    
    # Get transaction data using stored procedure
    try:
        with transaction(IsolationLevel.READ_COMMITTED) as (conn, cursor):
            cursor.execute(
                "CALL get_transaction_history(%s, %s, %s, %s)",
                [start_date, end_date, seller_id, buyer_id]
            )
            transactions = cursor.fetchall()
            
            # Make sure to consume any additional result sets
            while cursor.nextset():
                pass
            
            if not transactions:
                st.info("No transactions found for the selected period.")
                return
            
            # Create a DataFrame for easier analysis
            df = pd.DataFrame(transactions)
            
            # Display transaction counts and totals
            total_transactions = len(df)
            # Handle None values in price
            total_value = sum(float(t['price'] if t['price'] is not None else 0) for t in transactions)
            avg_price = total_value / total_transactions if total_transactions > 0 else 0
            
            # Display summary metrics with colored containers
            st.markdown("#### Transaction Summary")
            metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
            with metrics_col1:
                st.metric("Total Transactions", total_transactions)
            with metrics_col2:
                st.metric("Total Value", f"${total_value:.2f}")
            with metrics_col3:
                st.metric("Average Price", f"${avg_price:.2f}")
            
            # Transaction list with details
            st.markdown("#### Transaction Details")
            
            # Format the DataFrame for display
            if 'transaction_date' in df.columns:
                df['transaction_date'] = pd.to_datetime(df['transaction_date']).dt.strftime('%Y-%m-%d %H:%M')
            
            display_cols = ['transaction_id', 'transaction_date', 'item_title', 
                            'price', 'seller_name', 'buyer_name', 'status', 'payment_method']
            
            display_df = df[display_cols].rename(columns={
                'transaction_id': 'ID',
                'transaction_date': 'Date',
                'item_title': 'Item',
                'price': 'Price',
                'seller_name': 'Seller',
                'buyer_name': 'Buyer',
                'status': 'Status',
                'payment_method': 'Payment'
            })
            
            # Format the price column and handle None values
            display_df['Price'] = display_df['Price'].apply(lambda x: f"${float(x if x is not None else 0):.2f}")
            
            # Display the transactions table
            st.dataframe(display_df, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error retrieving transaction history: {str(e)}")

def app():
    reports_page()

if __name__ == "__main__":
    app()

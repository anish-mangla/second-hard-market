# secondhand_market/main.py

import streamlit as st
from database.db_setup import init_db, check_and_update_schema, get_connection
import pandas as pd

def home_page():
    # Initialize and update DB
    init_db()
    check_and_update_schema()

    # Page configuration
    st.set_page_config(
        page_title="SecondHand Market - Home",
        page_icon="🏪",
        layout="wide"
    )

    # Header with logo and title
    col1, col2 = st.columns([1, 3])
    with col1:
        st.image("https://cdn-icons-png.flaticon.com/512/3900/3900101.png", width=120)
    with col2:
        st.title("🏪 SecondHand Market")
        st.subheader("Buy, Sell, and Reuse Items in Your Community")
    
    st.markdown("---")
    
    # Feature highlights
    st.header("💡 Welcome to the Marketplace!")
    
    # Marketplace stats
    col1, col2, col3 = st.columns(3)
    
    # Get stats from the database
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        
        # Get total items
        cur.execute("SELECT COUNT(*) as count FROM items")
        total_items = cur.fetchone()['count']
        
        # Get available items
        cur.execute("SELECT COUNT(*) as count FROM items WHERE status = 'Available'")
        available_items = cur.fetchone()['count']
        
        # Get categories count
        cur.execute("SELECT COUNT(DISTINCT category) as count FROM items")
        categories = cur.fetchone()['count']
        
        cur.close()
        conn.close()
    except Exception:
        total_items = 0
        available_items = 0
        categories = 0
    
    with col1:
        st.metric("Total Items Listed", total_items)
    with col2:
        st.metric("Available Items", available_items)
    with col3:
        st.metric("Categories", categories)
    
    # Application features
    st.markdown("---")
    st.header("📱 Platform Features")
    
    features_col1, features_col2 = st.columns(2)
    
    with features_col1:
        st.subheader("🛒 For Buyers")
        st.markdown("""
        - Browse items by category, price, and condition
        - Search for specific items
        - Filter items by various criteria
        - Contact sellers directly
        - View detailed item information
        """)
    
    with features_col2:
        st.subheader("💰 For Sellers")
        st.markdown("""
        - List items with detailed descriptions
        - Upload images of your items
        - Set your preferred contact method
        - Track item status (Available, Pending, Sold)
        - Edit listings anytime
        """)
    
    # How to get started section
    st.markdown("---")
    st.header("🚀 How to Get Started")
    
    steps_col1, steps_col2, steps_col3 = st.columns(3)
    
    with steps_col1:
        st.markdown("### 1. Create an Item")
        st.markdown("""
        Navigate to the **Create Item** page to list something for sale.
        Add details, upload photos, and set your contact preference.
        """)
        if st.button("Go to Create Item →"):
            st.switch_page("pages/1_Create_Item.py")
    
    with steps_col2:
        st.markdown("### 2. Browse Items")
        st.markdown("""
        Visit the **View Items** page to browse available listings.
        Filter by category, price range, or use the search function.
        """)
        if st.button("Go to View Items →"):
            st.switch_page("pages/2_View_Items.py")
    
    with steps_col3:
        st.markdown("### 3. Check Reports")
        st.markdown("""
        Explore the **Reports** page to see marketplace analytics.
        View trends, popular categories, and price distributions.
        """)
        if st.button("Go to Reports →"):
            st.switch_page("pages/3_Reports.py")
    
    # About the project
    st.markdown("---")
    st.header("ℹ️ About This Project")
    st.markdown("""
    This SecondHand Market application was developed as a database-driven project for a database systems course.
    It demonstrates relational database concepts including:
    
    - Entity relationship modeling
    - SQL database design and normalization
    - Database queries and joins
    - Database schema evolution
    - Transaction management
    
    The application is built with Streamlit for the frontend and MySQL for the database.
    """)
    
    # Footer
    st.markdown("---")
    st.caption("© 2023 SecondHand Market | Database Systems Course Project")

if __name__ == "__main__":
    home_page()

# streamlit run main.py # use this to run
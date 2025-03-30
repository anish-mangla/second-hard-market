# secondhand_market/pages/2_View_Items.py

import streamlit as st
from database.db_setup import get_connection
import io
from PIL import Image
import base64
import datetime

def view_items_page():
    st.title("Browse Items")
    
    # Check if we have a specific item_id in query params
    query_params = st.query_params
    specific_item_id = query_params.get("item_id", [None])[0]
    
    # Search bar at the top
    search_query = st.text_input("🔍 Search items by keyword", placeholder="Enter keywords...")
    
    # Sidebar filters section
    st.sidebar.header("Filters")
    
    # Get all categories from the database
    con = get_connection()
    cur = con.cursor()
    cur.execute("SELECT DISTINCT category FROM items WHERE category IS NOT NULL")
    categories = [cat[0] for cat in cur.fetchall()]
    cur.close()
    
    # Filter by category
    selected_category = st.sidebar.selectbox(
        "Category", 
        ["All Categories"] + categories,
        index=0
    )
    
    # Filter by price range
    st.sidebar.subheader("Price Range")
    cur = con.cursor()
    cur.execute("SELECT MIN(price), MAX(price) FROM items")
    min_price, max_price = cur.fetchone()
    min_price = 0 if min_price is None else float(min_price)
    max_price = 1000 if max_price is None else float(max_price) + 100  # Add some buffer
    
    price_range = st.sidebar.slider(
        "Select price range",
        min_value=min_price,
        max_value=max_price,
        value=(min_price, max_price)
    )
    
    # Filter by condition
    conditions = ["All Conditions", "New", "Used - Like New", "Used - Good", "Used - Acceptable", "For parts"]
    selected_condition = st.sidebar.selectbox("Condition", conditions, index=0)
    
    # Filter by listing date
    st.sidebar.subheader("Listing Date")
    date_options = ["Any time", "Today", "This week", "This month"]
    selected_date_filter = st.sidebar.radio("Show items from:", date_options)
    
    # Build the query based on filters
    query = "SELECT i.*, u.username, u.email FROM items i LEFT JOIN users u ON i.seller_id = u.user_id WHERE 1=1"
    params = []
    
    # Category filter
    if selected_category != "All Categories":
        query += " AND i.category = %s"
        params.append(selected_category)
    
    # Price range filter
    query += " AND i.price BETWEEN %s AND %s"
    params.extend([price_range[0], price_range[1]])
    
    # Condition filter
    if selected_condition != "All Conditions":
        query += " AND i.condition_status = %s"
        params.append(selected_condition)
    
    # Date filter
    if selected_date_filter != "Any time":
        today = datetime.datetime.now().date()
        if selected_date_filter == "Today":
            query += " AND DATE(i.created_at) = %s"
            params.append(today)
        elif selected_date_filter == "This week":
            # Calculate start of week (Sunday or Monday depending on your preference)
            start_of_week = today - datetime.timedelta(days=today.weekday())
            query += " AND i.created_at >= %s"
            params.append(start_of_week)
        elif selected_date_filter == "This month":
            start_of_month = datetime.datetime(today.year, today.month, 1)
            query += " AND i.created_at >= %s"
            params.append(start_of_month)
    
    # Search query
    if search_query:
        query += " AND (i.title LIKE %s OR i.description LIKE %s)"
        search_param = f"%{search_query}%"
        params.extend([search_param, search_param])
    
    # If specific item_id is provided, filter just for that item
    if specific_item_id:
        query += " AND i.item_id = %s"
        params.append(specific_item_id)
    
    # Add sorting options in the main area
    sort_col1, sort_col2, sort_col3 = st.columns([2, 2, 1])
    
    with sort_col1:
        sort_options = {
            "Newest first": "i.created_at DESC",
            "Oldest first": "i.created_at ASC",
            "Price: Low to High": "i.price ASC",
            "Price: High to Low": "i.price DESC",
            "A-Z": "i.title ASC",
            "Z-A": "i.title DESC"
        }
        selected_sort = st.selectbox("Sort by:", list(sort_options.keys()))
    
    with sort_col2:
        # View options
        view_type = st.radio(
            "View as:",
            ["Grid", "List"],
            horizontal=True
        )
    
    # Complete the query with sorting
    query += f" ORDER BY {sort_options[selected_sort]}"
    
    # Pagination
    items_per_page = 8 if view_type == "List" else 6
    
    # Get total count first
    count_con = get_connection()
    count_cur = count_con.cursor()
    # Create a COUNT query based on the same WHERE clause
    count_query = query.replace("SELECT i.*, u.username, u.email", "SELECT COUNT(*)")
    count_query = count_query.split("ORDER BY")[0]  # Remove ORDER BY clause for count
    
    count_cur.execute(count_query, params)
    total_items = count_cur.fetchone()[0]
    count_cur.close()
    count_con.close()
    
    # Calculate pagination
    total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)
    
    with sort_col3:
        # Add 1 to make it 1-indexed for users
        current_page = st.number_input("Page", min_value=1, max_value=total_pages, value=1)
    
    # Adjust query for pagination
    current_page = int(current_page)  # Ensure it's an integer
    offset = (current_page - 1) * items_per_page
    query += f" LIMIT {items_per_page} OFFSET {offset}"
    
    # Display item count
    st.markdown(f"**Showing {min(items_per_page, total_items - offset)} of {total_items} items**")
    
    # Fetch items with pagination
    con = get_connection()
    cur = con.cursor(dictionary=True)
    cur.execute(query, params)
    items = cur.fetchall()
    cur.close()
    con.close()

    if not items:
        st.info("No items found matching your criteria.")
        return

    # Display items based on view type
    if view_type == "Grid":
        # Grid view (2 columns instead of 3 to make cards wider)
        cols = st.columns(2)
        
        for i, row in enumerate(items):
            with cols[i % 2]:
                with st.container():
                    # Create a card-like structure with better styling
                    st.markdown(f"""
                    <div style="border:1px solid #ddd; border-radius:10px; padding:15px; margin-bottom:20px; background-color:#f9f9f9;">
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Display in columns within the card for better layout
                    img_col, info_col = st.columns([1, 1])
                    
                    with img_col:
                        # Display image if available
                        if row.get('image_data'):
                            try:
                                image = Image.open(io.BytesIO(row['image_data']))
                                st.image(image, use_container_width=True)
                            except Exception:
                                st.warning("Image not available")
                    
                    with info_col:
                        # Item title and price
                        st.markdown(f"### {row['title']}")
                        st.markdown(f"**${float(row['price']):.2f}**")
                        
                        # Item metadata - condition and category
                        st.markdown(f"*{row['condition_status']}* | {row['category'] or 'Uncategorized'}")
                        
                        # Truncated description for grid view
                        description = row['description']
                        if len(description) > 80:
                            description = description[:77] + "..."
                        st.markdown(description)
                    
                    # Contact info and action buttons in a row
                    contact_col, detail_col = st.columns(2)
                    
                    with contact_col:
                        st.markdown(f"**Seller:** {row['username']}")
                        if row.get('email'):
                            st.markdown(f"**Contact:** {row['email']}")
                    
                    with detail_col:
                        # View details button
                        if st.button(f"View Details", key=f"view_{row['item_id']}"):
                            st.session_state.selected_item = row['item_id']
                    
                    # Show item details if selected
                    if hasattr(st.session_state, 'selected_item') and st.session_state.selected_item == row['item_id']:
                        with st.expander("Item Details", expanded=True):
                            display_item_details(row)
    else:
        # List view
        for row in items:
            with st.expander(f"{row['title']} (${float(row['price']):.2f}) - {row['username']}"):
                display_item_details(row)

    # Pagination controls
    pagination_cols = st.columns([1, 2, 1])
    with pagination_cols[1]:
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if current_page > 1:
                if st.button("← Previous"):
                    # Update query params for the previous page
                    st.query_params.page = current_page-1
                    st.rerun()
        
        with col2:
            st.markdown(f"**Page {current_page} of {total_pages}**", unsafe_allow_html=True)
            
        with col3:
            if current_page < total_pages:
                if st.button("Next →"):
                    # Update query params for the next page
                    st.query_params.page = current_page+1
                    st.rerun()

def display_item_details(row):
    """Helper function to display full item details"""
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Display image if available
        if row.get('image_data'):
            try:
                image = Image.open(io.BytesIO(row['image_data']))
                st.image(image, use_container_width=True)
            except Exception:
                st.warning("Image could not be displayed")
    
    with col2:
        # Display all item details
        st.markdown(f"### {row['title']}")
        st.markdown(f"**Price:** ${float(row['price']):.2f}")
        st.markdown(f"**Category:** {row['category'] or 'Not specified'}")
        st.markdown(f"**Condition:** {row['condition_status']}")
        
        # Seller information
        st.markdown(f"**Seller:** {row['username']}")
        if row.get('email'):
            st.markdown(f"**Contact:** {row['email']}")
        
        # Additional fields
        if row.get('location'):
            st.markdown(f"**Location:** {row['location']}")
        if row.get('contact_preference'):
            st.markdown(f"**Preferred Contact Method:** {row['contact_preference']}")
        
        st.markdown(f"**Status:** {row['status']}")
        st.markdown(f"**Listed on:** {row['created_at'].strftime('%B %d, %Y')}")
    
    # Full description section
    st.subheader("Description")
    st.markdown(row['description'])
    
    # Actions section
    st.subheader("Actions")
    col_contact, col_edit, col_delete = st.columns(3)
    
    with col_contact:
        contact_method = row.get('contact_preference', 'Email')
        contact_value = row.get('email', '')
        if st.button(f"Contact Seller", key=f"contact_{row['item_id']}"):
            st.info(f"Contact the seller via {contact_method}: {contact_value}")
            
    with col_edit:
        if st.button(f"Edit Item", key=f"edit_{row['item_id']}"):
            edit_item_form(row['item_id'])
            
    with col_delete:
        if st.button(f"Delete Item", key=f"delete_{row['item_id']}"):
            delete_item(row['item_id'])
            st.warning(f"Item {row['item_id']} deleted.")
            st.rerun()

def edit_item_form(item_id):
    st.subheader(f"Edit Item {item_id}")
    con = get_connection()
    cur = con.cursor(dictionary=True)
    cur.execute("SELECT * FROM items WHERE item_id = %s", (item_id,))
    item_data = cur.fetchone()
    cur.close()

    if not item_data:
        st.error("Item not found.")
        return

    with st.form(f"edit_item_form_{item_id}"):
        new_title = st.text_input("Title", item_data["title"])
        
        # Category selection
        categories = ["Electronics", "Clothing", "Furniture", "Books", "Sports & Outdoors", 
                      "Home & Kitchen", "Toys & Games", "Beauty & Health", "Other"]
        default_category_idx = categories.index(item_data["category"]) if item_data.get("category") in categories else 0
        new_category = st.selectbox("Category", categories, index=default_category_idx)
        
        new_description = st.text_area("Description", item_data["description"])
        
        # Two columns for price and condition
        col1, col2 = st.columns(2)
        with col1:
            new_price = st.number_input("Price", min_value=0.0, value=float(item_data["price"] or 0.0), format="%.2f")
        with col2:
            all_conditions = ["New", "Used - Like New", "Used - Good", "Used - Acceptable", "For parts"]
            default_idx = all_conditions.index(item_data["condition_status"]) if item_data["condition_status"] in all_conditions else 0
            new_condition = st.selectbox("Condition", all_conditions, index=default_idx)
        
        # Image upload (with current image preview if available)
        if item_data.get('image_data'):
            try:
                st.write("Current Image:")
                image = Image.open(io.BytesIO(item_data['image_data']))
                st.image(image, width=200)
            except Exception:
                st.warning("Current image could not be displayed")
        
        uploaded_file = st.file_uploader("Upload a new image (leave empty to keep current)", type=["jpg", "jpeg", "png"])
        
        # Contact and location
        new_contact = st.selectbox(
            "Preferred contact method", 
            ["Email", "Phone", "In-app messaging"],
            index=["Email", "Phone", "In-app messaging"].index(item_data.get("contact_preference", "Email"))
        )
        
        new_location = st.text_input("Location", item_data.get("location", ""))
        
        # Item status selection
        new_status = st.selectbox(
            "Item Status",
            ["Available", "Pending", "Sold"],
            index=["Available", "Pending", "Sold"].index(item_data.get("status", "Available"))
        )
        
        submitted = st.form_submit_button("Save Changes")
        if submitted:
            # Prepare query and parameters
            update_query = """
                UPDATE items
                SET title=%s, description=%s, price=%s, condition_status=%s, 
                    category=%s, contact_preference=%s, location=%s, status=%s
            """
            params = [new_title, new_description, new_price, new_condition, 
                     new_category, new_contact, new_location, new_status]
            
            # Handle image update if a new one is uploaded
            if uploaded_file is not None:
                update_query += ", image_data=%s"
                params.append(uploaded_file.getvalue())
            
            # Complete the query and execute
            update_query += " WHERE item_id=%s"
            params.append(item_id)
            
            upd_cur = con.cursor()
            upd_cur.execute(update_query, params)
            con.commit()
            upd_cur.close()
            con.close()

            st.success("Item updated successfully!")
            st.rerun()
        else:
            con.close()

def delete_item(item_id):
    # Confirm deletion with a modal
    if 'confirm_delete' not in st.session_state:
        st.session_state.confirm_delete = False
    
    if not st.session_state.confirm_delete:
        st.warning("Are you sure you want to delete this item? This cannot be undone.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Cancel"):
                st.session_state.confirm_delete = False
                return
        with col2:
            if st.button("Yes, Delete It"):
                st.session_state.confirm_delete = True
    
    if st.session_state.confirm_delete:
        # Proceed with deletion
        con = get_connection()
        cur = con.cursor()
        cur.execute("DELETE FROM items WHERE item_id = %s", (item_id,))
        con.commit()
        cur.close()
        con.close()
        st.success("Item deleted successfully!")
        st.session_state.confirm_delete = False
        # Delay the rerun slightly to show the success message
        st.rerun()

def app():
    # Initialize session state for selected item if not exists
    if 'selected_item' not in st.session_state:
        st.session_state.selected_item = None
        
    view_items_page()

if __name__ == "__main__":
    app()

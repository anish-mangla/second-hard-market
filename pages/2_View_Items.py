# secondhand_market/pages/2_View_Items.py

import streamlit as st
from database.db_setup import get_connection
import io
from PIL import Image
import base64
import datetime
from database.create_procedures import create_procedures
from database.transaction_manager import transaction, IsolationLevel, update_item_status_safely

def view_items_page():
    st.title("Browse Items")
    
    # Ensure stored procedures exist
    create_procedures()
    
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
    
    # Add status filter
    status_options = ["All", "Available", "Pending", "Sold"]
    selected_status = st.sidebar.selectbox("Status", status_options, index=0)
    
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
    
    # Build the query based on filters
    params = []
    items = []
    total_items = 0
    
    # If there's a specific item ID, we use a direct query instead of stored procedure
    if specific_item_id:
        query = "SELECT i.*, u.username, u.email FROM items i LEFT JOIN users u ON i.seller_id = u.user_id WHERE i.item_id = %s"
        params = [specific_item_id]
        
        con = get_connection()
        cur = con.cursor(dictionary=True)
        cur.execute(query, params)
        items = cur.fetchall()
        total_items = len(items)
        cur.close()
        con.close()
    else:
        # Using stored procedure for basic filtering
        if selected_category == "All Categories":
            category_param = None
        else:
            category_param = selected_category
            
        status_param = None if selected_status == "All" else selected_status
        
        # Get filtered items using stored procedure
        con = get_connection()
        cur = con.cursor(dictionary=True)
        
        # Date filter
        date_filter_query = ""
        date_params = []
        
        if selected_date_filter != "Any time":
            today = datetime.datetime.now().date()
            if selected_date_filter == "Today":
                date_filter_query = " AND DATE(i.created_at) = %s"
                date_params = [today]
            elif selected_date_filter == "This week":
                # Calculate start of week (Sunday or Monday depending on your preference)
                start_of_week = today - datetime.timedelta(days=today.weekday())
                date_filter_query = " AND i.created_at >= %s"
                date_params = [start_of_week]
            elif selected_date_filter == "This month":
                start_of_month = datetime.datetime(today.year, today.month, 1)
                date_filter_query = " AND i.created_at >= %s"
                date_params = [start_of_month]
        
        # Search query
        search_filter = ""
        search_params = []
        
        if search_query:
            search_filter = " AND (i.title LIKE %s OR i.description LIKE %s)"
            search_param = f"%{search_query}%"
            search_params = [search_param, search_param]
        
        # Call stored procedure for basic filtering
        if not date_filter_query and not search_filter:
            # We can use the stored procedure directly
            cur.execute(
                "CALL get_items_by_filter(%s, %s, %s, %s, %s)", 
                [category_param, price_range[0], price_range[1], selected_condition, status_param]
            )
            items = cur.fetchall()
            
            # Count items (reopen cursor since stored procedure closes it)
            total_items = len(items)
        else:
            # Need to use standard query to combine with search and date filters
            query = """
                SELECT i.*, u.username, u.email 
                FROM items i 
                LEFT JOIN users u ON i.seller_id = u.user_id 
                WHERE 1=1
                    AND (i.category = %s OR %s IS NULL OR %s = 'All Categories')
                    AND (i.price BETWEEN %s AND %s)
                    AND (i.condition_status = %s OR %s IS NULL OR %s = 'All Conditions')
                    AND (i.status = %s OR %s IS NULL OR %s = 'All')
            """
            params = [
                category_param, category_param, category_param,
                price_range[0], price_range[1],
                selected_condition, selected_condition, selected_condition,
                status_param, status_param, status_param
            ]
            
            # Add date filter if needed
            if date_filter_query:
                query += date_filter_query
                params.extend(date_params)
                
            # Add search filter if needed
            if search_filter:
                query += search_filter
                params.extend(search_params)
                
            # Add sorting
            query += f" ORDER BY {sort_options[selected_sort]}"
            
            # Get count first
            count_query = query.replace("i.*, u.username, u.email", "COUNT(*)")
            count_query = count_query.split("ORDER BY")[0]
            
            cur.execute(count_query, params)
            total_items = cur.fetchone()['COUNT(*)']
            
            # Pagination
            items_per_page = 8 if view_type == "List" else 6
            total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)
            
            with sort_col3:
                # Add 1 to make it 1-indexed for users
                current_page = st.number_input("Page", min_value=1, max_value=total_pages, value=1)
            
            # Adjust query for pagination
            current_page = int(current_page)  # Ensure it's an integer
            offset = (current_page - 1) * items_per_page
            query += f" LIMIT {items_per_page} OFFSET {offset}"
            
            # Execute query with pagination
            cur.execute(query, params)
            items = cur.fetchall()
        
        cur.close()
        con.close()
    
    # Display item count
    st.markdown(f"**Showing {len(items)} of {total_items} items**")
    
    if not items:
        st.info("No items found matching your criteria.")
        return

    # CSS for the cards
    st.markdown("""
    <style>
    .item-card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 20px;
        background-color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        overflow: hidden;
    }
    .item-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    }
    .status-badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: bold;
        color: white;
        margin-right: 8px;
    }
    .status-available {
        background-color: #28a745;
    }
    .status-pending {
        background-color: #ffc107;
        color: #212529;
    }
    .status-sold {
        background-color: #dc3545;
    }
    .price-tag {
        font-size: 1.3rem;
        font-weight: bold;
        color: #1E5C37;
    }
    .condition-tag {
        font-size: 0.85rem;
        color: #666;
        margin-bottom: 8px;
    }
    .item-title {
        margin-top: 5px;
        margin-bottom: 10px;
        font-size: 1.2rem;
        font-weight: bold;
        color: #333;
    }
    .item-description {
        color: #555;
        font-size: 0.9rem;
        margin-bottom: 10px;
    }
    .meta-info {
        font-size: 0.8rem;
        color: #777;
    }
    .view-details-btn {
        margin-top: 10px;
    }
    .action-button {
        border-radius: 20px;
        padding: 5px 10px;
        font-size: 0.9rem;
        border: none;
    }
    </style>
    """, unsafe_allow_html=True)

    # Display items based on view type
    if view_type == "Grid":
        # Grid view (2 columns)
        cols = st.columns(2)
        
        for i, row in enumerate(items):
            with cols[i % 2]:
                with st.container():
                    # Create a card structure with CSS styling
                    st.markdown('<div class="item-card">', unsafe_allow_html=True)
                    
                    # Status badge
                    status_class = f"status-{row['status'].lower()}" if row['status'] in ['Available', 'Pending', 'Sold'] else "status-available"
                    st.markdown(f'<span class="status-badge {status_class}">{row["status"]}</span>', unsafe_allow_html=True)
                    
                    # Display in columns within the card for better layout
                    img_col, info_col = st.columns([1, 1])
                    
                    with img_col:
                        # Display image if available
                        if row.get('image_data'):
                            try:
                                image = Image.open(io.BytesIO(row['image_data']))
                                st.image(image, use_container_width=True)
                            except Exception:
                                st.markdown("📷 Image not available")
                        else:
                            st.markdown("📷 No image")
                    
                    with info_col:
                        # Item title
                        st.markdown(f'<div class="item-title">{row["title"]}</div>', unsafe_allow_html=True)
                        
                        # Price tag
                        st.markdown(f'<div class="price-tag">${float(row["price"]):.2f}</div>', unsafe_allow_html=True)
                        
                        # Condition and category
                        st.markdown(f'<div class="condition-tag">{row["condition_status"]} | {row["category"] or "Uncategorized"}</div>', unsafe_allow_html=True)
                        
                        # Truncated description
                        description = row['description']
                        if len(description) > 80:
                            description = description[:77] + "..."
                        st.markdown(f'<div class="item-description">{description}</div>', unsafe_allow_html=True)
                    
                    # Footer with seller info and action button
                    st.markdown(f'<div class="meta-info">📅 Listed: {row["created_at"].strftime("%b %d, %Y")}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="meta-info">👤 Seller: {row["username"]}</div>', unsafe_allow_html=True)
                    
                    # View details button
                    if st.button(f"View Details", key=f"view_{row['item_id']}", use_container_width=True):
                        st.session_state.selected_item = row['item_id']
                    
                    # Show item details if selected
                    if hasattr(st.session_state, 'selected_item') and st.session_state.selected_item == row['item_id']:
                        with st.expander("Item Details", expanded=True):
                            display_item_details(row)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
    else:
        # List view
        for row in items:
            # Status badge HTML for list view
            status_class = f"status-{row['status'].lower()}" if row['status'] in ['Available', 'Pending', 'Sold'] else "status-available"
            status_badge = f'<span class="status-badge {status_class}">{row["status"]}</span>'
            
            # Create list item with status badge
            with st.expander(f"{status_badge} {row['title']} (${float(row['price']):.2f}) - {row['username']}", expanded=False):
                display_item_details(row)

    # Pagination controls if not specific item
    if not specific_item_id and 'total_pages' in locals() and total_pages > 1:
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
        else:
            st.info("No image available")
    
    with col2:
        # Create status badge HTML
        status_class = f"status-{row['status'].lower()}" if row['status'] in ['Available', 'Pending', 'Sold'] else "status-available"
        status_badge = f'<span class="status-badge {status_class}">{row["status"]}</span>'
        
        # Display all item details with the status badge
        st.markdown(f"### {row['title']} {status_badge}", unsafe_allow_html=True)
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
            st.session_state.show_edit_form = True
            st.session_state.item_to_edit = row['item_id']
            st.rerun()
            
    with col_delete:
        if st.button(f"Delete Item", key=f"delete_{row['item_id']}"):
            st.session_state.show_delete_confirmation = True
            st.session_state.item_to_delete = row['item_id']
            st.rerun()

def edit_item_form(item_id):
    """Show form to edit an item"""
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
        
        # Use form layout without nested columns
        new_price = st.number_input("Price", min_value=0.0, value=float(item_data["price"] or 0.0), format="%.2f")
        
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
        cancel = st.form_submit_button("Cancel")
        
        if cancel:
            st.session_state.show_edit_form = False
            st.rerun()
            
        if submitted:
            try:
                # Use transaction for item update with REPEATABLE READ isolation
                with transaction(IsolationLevel.REPEATABLE_READ) as (conn, cursor):
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
                    
                    cursor.execute(update_query, params)
                    conn.commit()

                st.success("Item updated successfully!")
                # Clear the edit form state
                st.session_state.show_edit_form = False
                # Add a small delay to show the success message
                import time
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Error updating item: {str(e)}")
        else:
            con.close()

def delete_item(item_id):
    """Delete an item after confirmation"""
    try:
        # Use a transaction with SERIALIZABLE isolation to ensure data consistency
        with transaction(IsolationLevel.SERIALIZABLE) as (conn, cursor):
            # Check if the item exists and can be deleted
            cursor.execute("SELECT status FROM items WHERE item_id = %s FOR UPDATE", (item_id,))
            item = cursor.fetchone()
            
            if not item:
                st.error(f"Item {item_id} not found")
                return False
            
            # Perform the deletion
            cursor.execute("DELETE FROM items WHERE item_id = %s", (item_id,))
            
            if cursor.rowcount > 0:
                return True
            else:
                st.error("Failed to delete item")
                return False
    except Exception as e:
        st.error(f"Error deleting item: {str(e)}")
        return False

def app():
    # Initialize session state if not exists
    if 'selected_item' not in st.session_state:
        st.session_state.selected_item = None
        
    # Show edit form if flag is set (before any other UI elements)
    if 'show_edit_form' in st.session_state and st.session_state.show_edit_form:
        item_id = st.session_state.item_to_edit
        edit_item_form(item_id)
        # Add a "Back to browsing" button
        if st.button("Back to browsing without saving"):
            st.session_state.show_edit_form = False
            st.rerun()
        return  # Exit early to not show the main page
    
    # Show delete confirmation dialog if flag is set
    if 'show_delete_confirmation' in st.session_state and st.session_state.show_delete_confirmation:
        item_id = st.session_state.item_to_delete
        
        # Create a container for the confirmation dialog to make it more prominent
        with st.container():
            st.warning(f"⚠️ Are you sure you want to delete this item? This action cannot be undone.")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Cancel", key="cancel_delete_final"):
                    # Clear the confirmation state and rerun
                    st.session_state.show_delete_confirmation = False
                    del st.session_state.item_to_delete
                    st.rerun()
                    
            with col2:
                if st.button("Yes, Delete It", key="confirm_delete_final", type="primary"):
                    # Perform the actual deletion
                    success = delete_item(item_id)
                    
                    if success:
                        st.success("Item deleted successfully!")
                        # Clear the confirmation state
                        st.session_state.show_delete_confirmation = False
                        del st.session_state.item_to_delete
                        # Add a small delay to show the success message
                        import time
                        time.sleep(1)
                        st.rerun()
        return  # Exit early to not show the main page
    
    view_items_page()

if __name__ == "__main__":
    app()

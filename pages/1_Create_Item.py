# secondhand_market/pages/1_Create_Item.py

import streamlit as st
import datetime
from database.db_setup import get_connection
from database.orm_models import get_session, User, Item
import base64
from PIL import Image
import io
from decimal import Decimal
from database.transaction_manager import transaction, IsolationLevel, sqlalchemy_transaction

def get_user_info(user_id):
    """Get the user information for the current user using ORM"""
    session = get_session()
    user = session.query(User).filter(User.user_id == user_id).first()
    session.close()
    return user

def update_user_contact(user_id, email, phone):
    """Update the user's contact information if changed using ORM"""
    session = get_session()
    user = session.query(User).filter(User.user_id == user_id).first()
    if user:
        user.email = email
        user.phone = phone
        session.commit()
    session.close()

def create_item_page():
    st.title("Create a New Item")
    st.write("Fill out the form below to list your item on the marketplace.")

    # Hardcode seller_id=1 for now or handle user login in a future step.
    seller_id = 1
    
    # Get current user data using ORM
    user_data = get_user_info(seller_id)
    
    # Create two columns for the form
    col1, col2 = st.columns([2, 1])

    with col1:
        # Seller information section
        st.subheader("Your Contact Information")
        seller_email = st.text_input("Email Address", value=user_data.email if user_data and user_data.email else '')
        seller_phone = st.text_input("Phone Number", value=user_data.phone if user_data and user_data.phone else '')
        
        # Update user contact info if provided
        if seller_email or seller_phone:
            update_user_contact(seller_id, seller_email, seller_phone)
            
        st.subheader("Item Details")
        
        with st.form("create_item_form"):
            # Basic item information
            title = st.text_input("Title*", help="Give your item a clear, descriptive title")
            
            # Category selection
            category = st.selectbox(
                "Category*", 
                ["Electronics", "Clothing", "Furniture", "Books", "Sports & Outdoors", 
                 "Home & Kitchen", "Toys & Games", "Beauty & Health", "Other"]
            )
            
            description = st.text_area("Description*", help="Describe your item, include details about features and condition")
            
            # Price and condition
            col_price, col_cond = st.columns(2)
            with col_price:
                price = st.number_input("Price ($)*", min_value=0.0, format="%.2f")
            with col_cond:
                condition_status = st.selectbox(
                    "Condition*", 
                    ["New", "Used - Like New", "Used - Good", "Used - Acceptable", "For parts"]
                )
            
            # Image upload
            uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
            image_data = None
            if uploaded_file is not None:
                # Convert to bytes for storage
                image_data = uploaded_file.getvalue()
            
            # Contact preference
            contact_preference = st.radio(
                "Preferred contact method",
                ["Email", "Phone", "In-app messaging"]
            )
            
            # Location information
            location = st.text_input("Location", help="Where can the buyer pick up this item?")
            
            # Fields marked with * are required
            st.markdown("*Required fields")
            
            submitted = st.form_submit_button("Create Item")
            if submitted:
                if not title or not description or price <= 0:
                    st.error("Please fill out all required fields.")
                elif contact_preference == "Email" and not seller_email:
                    st.error("You selected Email as your preferred contact method but didn't provide an email address.")
                elif contact_preference == "Phone" and not seller_phone:
                    st.error("You selected Phone as your preferred contact method but didn't provide a phone number.")
                else:
                    try:
                        # Convert form data
                        price_float = float(price)
                        
                        # Process image
                        image_data = None
                        if uploaded_file is not None:
                            image_data = uploaded_file.getvalue()
                        
                        # Create new item using SQLAlchemy transaction with SERIALIZABLE isolation
                        session = get_session()
                        
                        with sqlalchemy_transaction(session, IsolationLevel.SERIALIZABLE) as session:
                            # Verify seller exists
                            seller = session.query(User).filter(User.user_id == seller_id).first()
                            
                            if not seller:
                                st.error(f"Seller ID {seller_id} does not exist")
                                return
                            
                            # Create new item
                            new_item = Item(
                                title=title,
                                description=description,
                                price=Decimal(str(price_float)),
                                condition_status=condition_status,
                                seller_id=seller_id,
                                category=category,
                                contact_preference=contact_preference,
                                location=location,
                                image_data=image_data
                            )
                            
                            session.add(new_item)
                            # Transaction will be committed at the end of the context manager
                        
                        st.success(f"Item '{title}' successfully created!")
                        st.balloons()
                        
                        # Clear form
                        st.session_state["title"] = ""
                        st.session_state["description"] = ""
                        st.session_state["price"] = ""
                        st.session_state["uploaded_file"] = None
                        
                        # Add a flag to session state to indicate we should redirect
                        st.session_state["item_created"] = True
                    except Exception as e:
                        st.error(f"Error creating item: {str(e)}")
                        st.error("Please try again or contact support if the issue persists.")

    # Preview column
    with col2:
        st.subheader("Item Preview")
        st.markdown("---")
        
        # Show preview of the item as the user fills the form
        if 'title' in locals() and title:
            st.markdown(f"### {title}")
        
        if 'price' in locals() and price > 0:
            st.markdown(f"**${price:.2f}**")
            
        if 'condition_status' in locals() and condition_status:
            st.markdown(f"*Condition: {condition_status}*")
            
        if 'category' in locals() and category:
            st.markdown(f"Category: {category}")
        
        # Display image preview if uploaded
        if 'uploaded_file' in locals() and uploaded_file is not None:
            try:
                image = Image.open(io.BytesIO(uploaded_file))
                st.image(image, caption="Item image", use_container_width=True)
            except Exception:
                st.error("Could not display image preview.")
        
        if 'location' in locals() and location:
            st.markdown(f"**Location:** {location}")
            
        if 'contact_preference' in locals() and contact_preference:
            contact_value = ""
            if contact_preference == "Email" and 'seller_email' in locals():
                contact_value = seller_email
            elif contact_preference == "Phone" and 'seller_phone' in locals():
                contact_value = seller_phone
            
            st.markdown(f"**Contact via:** {contact_preference} ({contact_value})")
                
        st.markdown("---")
        st.markdown("*This is how your item will appear to buyers*")

    # Navigation button outside the form
    if "item_created" in st.session_state and st.session_state["item_created"]:
        st.session_state["item_created"] = False  # Reset the flag
        st.success("Redirecting to View Items page...")
        st.switch_page("pages/2_View_Items.py")

def app():
    create_item_page()

if __name__ == "__main__":
    app()

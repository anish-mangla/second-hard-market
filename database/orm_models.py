from sqlalchemy import create_engine, Column, Integer, String, Numeric, DateTime, Text, ForeignKey, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref
import os
from datetime import datetime
from database.db_setup import DB_NAME
import urllib.parse

# Define your MySQL connection string
# Get MySQL credentials from environment or use defaults
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'Kkhiladi@420')

# URL encode the password to handle special characters like @
encoded_password = urllib.parse.quote_plus(DB_PASSWORD)

# Create SQLAlchemy engine and session
connection_string = f"mysql+mysqlconnector://{DB_USER}:{encoded_password}@{DB_HOST}/{DB_NAME}"
engine = create_engine(connection_string)
Session = sessionmaker(bind=engine)

# Create base class for models
Base = declarative_base()

class User(Base):
    """ORM model for the users table"""
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    password_hash = Column(String(255))
    
    # Relationships
    items = relationship("Item", back_populates="seller")
    sold_transactions = relationship("Transaction", foreign_keys="Transaction.seller_id", back_populates="seller")
    purchased_transactions = relationship("Transaction", foreign_keys="Transaction.buyer_id", back_populates="buyer")
    
    def __repr__(self):
        return f"<User(user_id={self.user_id}, username='{self.username}')>"

class Category(Base):
    """ORM model for the categories table"""
    __tablename__ = 'categories'
    
    category_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    parent_category_id = Column(Integer, ForeignKey('categories.category_id'))
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    items = relationship("Item", back_populates="category")
    subcategories = relationship(
        "Category", 
        backref=backref("parent_category", remote_side=[category_id]),
        foreign_keys=[parent_category_id]
    )
    
    def __repr__(self):
        return f"<Category(category_id={self.category_id}, name='{self.name}')>"

class Item(Base):
    """ORM model for the items table"""
    __tablename__ = 'items'
    
    item_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(Numeric(10, 2))
    condition_status = Column(String(50))
    created_at = Column(DateTime, default=datetime.now)
    status = Column(String(50), default='Available')
    seller_id = Column(Integer, ForeignKey('users.user_id'))
    category_id = Column(Integer, ForeignKey('categories.category_id'))
    contact_preference = Column(String(50))
    location = Column(String(255))
    image_data = Column(LargeBinary)
    
    # Relationships
    seller = relationship("User", back_populates="items")
    category = relationship("Category", back_populates="items")
    transactions = relationship("Transaction", back_populates="item")
    
    def __repr__(self):
        return f"<Item(item_id={self.item_id}, title='{self.title}', price={self.price})>"

class Transaction(Base):
    """ORM model for the transactions table"""
    __tablename__ = 'transactions'
    
    transaction_id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(Integer, ForeignKey('items.item_id'), nullable=False)
    seller_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    buyer_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    transaction_date = Column(DateTime, default=datetime.now)
    price = Column(Numeric(10, 2), nullable=False)
    status = Column(String(50), default='Completed')
    payment_method = Column(String(50))
    notes = Column(Text)
    
    # Relationships
    item = relationship("Item", back_populates="transactions")
    seller = relationship("User", foreign_keys=[seller_id], back_populates="sold_transactions")
    buyer = relationship("User", foreign_keys=[buyer_id], back_populates="purchased_transactions")
    
    def __repr__(self):
        return f"<Transaction(id={self.transaction_id}, item_id={self.item_id}, price={self.price})>"

# Function to get a new session
def get_session():
    """Return a new SQLAlchemy session"""
    return Session()

# Function to create tables if they don't exist
def create_tables():
    """Create all tables defined by the models"""
    Base.metadata.create_all(engine) 
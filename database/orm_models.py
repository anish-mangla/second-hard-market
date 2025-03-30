from sqlalchemy import create_engine, Column, Integer, String, Numeric, DateTime, Text, ForeignKey, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
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
    
    # Relationship to items (one-to-many)
    items = relationship("Item", back_populates="seller")
    
    def __repr__(self):
        return f"<User(user_id={self.user_id}, username='{self.username}')>"

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
    category = Column(String(100))
    contact_preference = Column(String(50))
    location = Column(String(255))
    image_data = Column(LargeBinary)
    
    # Relationship to user (many-to-one)
    seller = relationship("User", back_populates="items")
    
    def __repr__(self):
        return f"<Item(item_id={self.item_id}, title='{self.title}', price={self.price})>"

# Function to get a new session
def get_session():
    """Return a new SQLAlchemy session"""
    return Session()

# Function to create tables if they don't exist
def create_tables():
    """Create all tables defined by the models"""
    Base.metadata.create_all(engine) 
# insert_sample_data.py
import mysql.connector
from database.db_setup import get_connection, init_db, check_and_update_schema
import random
from datetime import datetime, timedelta
import os
import io
from PIL import Image
import requests

# Make sure the database is initialized first
init_db()
check_and_update_schema()

# Sample data for different categories
sample_data = {
    "Electronics": [
        {
            "title": "iPhone 11 Pro - Great Condition",
            "description": "iPhone 11 Pro 64GB Space Gray. In excellent condition with minimal scratches. Battery health at 89%. Comes with original charger and box. No longer needed as I've upgraded to a newer model.",
            "price": 399.99,
            "condition": "Used - Like New",
            "location": "Downtown",
            "contact_preference": "Email",
            "image_url": "https://images.unsplash.com/photo-1591337676887-a217a6970a8a?w=500"
        },
        {
            "title": "Sony Wireless Noise-Cancelling Headphones",
            "description": "Sony WH-1000XM4 wireless headphones. Purchased 8 months ago for $349. These are amazing headphones with industry-leading noise cancellation. Selling because I received a new pair as a gift. Comes with carrying case and all cables.",
            "price": 199.50,
            "condition": "Used - Good",
            "location": "North Campus",
            "contact_preference": "Phone",
            "image_url": "https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=500"
        },
        {
            "title": "Dell XPS 13 Laptop - 2020 Model",
            "description": "Dell XPS 13 from 2020. i5 processor, 8GB RAM, 256GB SSD. Battery lasts about 6 hours. Has a small dent on the bottom corner but works perfectly. Great for students or professionals. Includes charger.",
            "price": 580.00,
            "condition": "Used - Good",
            "location": "Westside",
            "contact_preference": "Email",
            "image_url": "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=500"
        },
        {
            "title": "Nintendo Switch with Games",
            "description": "Nintendo Switch console (original model) with 3 games: Zelda: Breath of the Wild, Mario Kart 8, and Animal Crossing. Comes with all accessories and original box. Works perfectly, just don't use it anymore.",
            "price": 240.00,
            "condition": "Used - Good",
            "location": "University Area",
            "contact_preference": "In-app messaging",
            "image_url": "https://images.unsplash.com/photo-1580327344181-c1163234e5a0?w=500"
        }
    ],
    "Furniture": [
        {
            "title": "IKEA MALM Dresser - White",
            "description": "IKEA MALM 6-drawer dresser in white. Purchased 2 years ago for $179. In good condition with some minor scratches on the top. Dimensions: 63\" height, 31.5\" width, 19\" depth. Must pick up yourself.",
            "price": 85.00,
            "condition": "Used - Good",
            "location": "Eastside",
            "contact_preference": "Phone",
            "image_url": "https://images.unsplash.com/photo-1595428774223-ef52624120d2?w=500"
        },
        {
            "title": "Solid Wood Coffee Table",
            "description": "Beautiful solid oak coffee table in mid-century modern style. Dimensions: 42\" length, 24\" width, 17\" height. Some minor scratches but overall in excellent condition. Downsizing my apartment and no longer have space for it.",
            "price": 120.00,
            "condition": "Used - Good",
            "location": "South Campus",
            "contact_preference": "Email",
            "image_url": "https://images.unsplash.com/photo-1634712282287-14ed57b9cc89?w=500"
        },
        {
            "title": "Desk Chair - Ergonomic",
            "description": "High-quality ergonomic desk chair with adjustable height, armrests, and lumbar support. Black mesh back for breathability. Used for only 1 year. Moving out of state and can't take it with me.",
            "price": 65.00,
            "condition": "Used - Like New",
            "location": "Downtown",
            "contact_preference": "Phone",
            "image_url": "https://images.unsplash.com/photo-1589884629108-3193400c7cc9?w=500"
        }
    ],
    "Clothing": [
        {
            "title": "Nike Air Jordan 1 - Size 10",
            "description": "Nike Air Jordan 1 Mid in Chicago colorway. Men's size 10. Worn only a few times and in excellent condition. Original box included. Selling because they're slightly too small for me.",
            "price": 120.00,
            "condition": "Used - Like New",
            "location": "Campus Area",
            "contact_preference": "Email",
            "image_url": "https://images.unsplash.com/photo-1556906781-9a412961c28c?w=500"
        },
        {
            "title": "Women's North Face Winter Jacket - Size M",
            "description": "Women's North Face Gotham Jacket III in black, size medium. Very warm with down insulation, perfect for winter. Used for one season and in excellent condition. Originally $300, selling because I moved to a warmer climate.",
            "price": 145.00,
            "condition": "Used - Good",
            "location": "Northside",
            "contact_preference": "Phone",
            "image_url": "https://images.unsplash.com/photo-1548126032-079a0fb0099d?w=500"
        },
        {
            "title": "Men's Dress Shirts Bundle - Size L",
            "description": "Bundle of 5 men's dress shirts, all size large, brands include Calvin Klein and Ralph Lauren. All in good condition, no stains or tears. Selling because I no longer work in an office environment.",
            "price": 60.00,
            "condition": "Used - Good",
            "location": "West Campus",
            "contact_preference": "In-app messaging",
            "image_url": "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=500"
        }
    ],
    "Books": [
        {
            "title": "Computer Science Textbook Bundle",
            "description": "Bundle of 4 computer science textbooks: 'Introduction to Algorithms', 'Computer Networks', 'Database System Concepts', and 'Artificial Intelligence: A Modern Approach'. All in good condition with minimal highlighting.",
            "price": 85.00,
            "condition": "Used - Good",
            "location": "University Library",
            "contact_preference": "Email",
            "image_url": "https://images.unsplash.com/photo-1544383835-bda2bc66a55d?w=500"
        },
        {
            "title": "Game of Thrones Complete Book Series",
            "description": "Complete 'A Song of Ice and Fire' book series by George R.R. Martin (5 books). Paperback, good condition with normal wear. Great fantasy series!",
            "price": 25.00,
            "condition": "Used - Good",
            "location": "South Campus",
            "contact_preference": "Phone",
            "image_url": "https://images.unsplash.com/photo-1541963463532-d68292c34b19?w=500"
        }
    ],
    "Sports & Outdoors": [
        {
            "title": "Trek Mountain Bike - 18\" Frame",
            "description": "Trek Marlin 5 mountain bike with 18\" frame (fits 5'8\"-5'11\" riders). 27.5\" wheels, hydraulic disc brakes, 3x8 gears. Used for two seasons but still in great shape. Selling because I'm upgrading to a full-suspension bike.",
            "price": 350.00,
            "condition": "Used - Good",
            "location": "East Campus",
            "contact_preference": "Phone",
            "image_url": "https://images.unsplash.com/photo-1511994298241-608e28f14fde?w=500"
        },
        {
            "title": "Camping Tent - 4 Person",
            "description": "Coleman 4-person dome tent. Used for only 3 weekend trips. Waterproof, easy setup, includes rainfly and carrying bag. Great for family camping or festivals.",
            "price": 65.00,
            "condition": "Used - Like New",
            "location": "Westside",
            "contact_preference": "Email",
            "image_url": "https://images.unsplash.com/photo-1504280390367-361c6d9f38f4?w=500"
        }
    ],
    "Home & Kitchen": [
        {
            "title": "Cuisinart Food Processor",
            "description": "Cuisinart 8-cup food processor. Works perfectly for chopping, slicing, shredding, and making dough. Includes all attachments and original box. Only used a few times.",
            "price": 45.00,
            "condition": "Used - Like New",
            "location": "Downtown",
            "contact_preference": "Email",
            "image_url": "https://images.unsplash.com/photo-1590794056226-79ef3a8147e1?w=500"
        },
        {
            "title": "Espresso Machine - Breville",
            "description": "Breville Barista Express espresso machine. Makes amazing espresso at home. Includes built-in grinder, steam wand, and all accessories. 2 years old but well maintained and cleaned regularly.",
            "price": 375.00,
            "condition": "Used - Good",
            "location": "North Campus",
            "contact_preference": "Phone",
            "image_url": "https://images.unsplash.com/photo-1570087935627-74d80ef32efd?w=500"
        }
    ],
    "Toys & Games": [
        {
            "title": "LEGO Star Wars Millennium Falcon",
            "description": "LEGO Star Wars Millennium Falcon set #75257. 100% complete with all pieces, minifigures, and instructions. No box. Built once and displayed, now dismantled and ready for a new home.",
            "price": 90.00,
            "condition": "Used - Like New",
            "location": "South Campus",
            "contact_preference": "Email",
            "image_url": "https://images.unsplash.com/photo-1585366119957-e9730b6d0f60?w=500"
        },
        {
            "title": "Board Game Collection (5 Games)",
            "description": "Collection of 5 popular board games: Catan, Ticket to Ride, Pandemic, Carcassonne, and Dominion. All complete with all pieces and in good condition. Selling as a bundle only.",
            "price": 110.00,
            "condition": "Used - Good",
            "location": "Eastside",
            "contact_preference": "In-app messaging",
            "image_url": "https://images.unsplash.com/photo-1610890716171-6b1bb98ffd09?w=500"
        }
    ],
    "Beauty & Health": [
        {
            "title": "Dyson Hair Dryer",
            "description": "Dyson Supersonic hair dryer in fuchsia/nickel. Includes all attachments and original box. Works perfectly, I'm just upgrading to a newer model. Originally $400, selling for less than half price.",
            "price": 180.00,
            "condition": "Used - Good",
            "location": "West Campus",
            "contact_preference": "Phone",
            "image_url": "https://images.unsplash.com/photo-1522338140262-f46f5913618a?w=500"
        }
    ],
    "Other": [
        {
            "title": "Telescope for Stargazing",
            "description": "Celestron PowerSeeker 70EQ telescope. Perfect for beginners interested in astronomy. Includes tripod, two eyepieces, and star diagonal. Used only a few times and in excellent condition.",
            "price": 85.00,
            "condition": "Used - Like New",
            "location": "College Hills",
            "contact_preference": "Email",
            "image_url": "https://images.unsplash.com/photo-1545156521-77bd85671d30?w=500"
        },
        {
            "title": "Vintage Record Player",
            "description": "Vintage Crosley record player in working condition. Has built-in speakers and can also connect to external speakers. Plays 33, 45, and 78 RPM records. Great retro piece with good sound quality.",
            "price": 75.00,
            "condition": "Used - Good",
            "location": "Downtown",
            "contact_preference": "Phone",
            "image_url": "https://images.unsplash.com/photo-1603048588665-791ca8aea617?w=500"
        }
    ]
}

def download_image(url):
    """Download an image from a URL and return as bytes"""
    try:
        response = requests.get(url, stream=True, timeout=10)
        if response.status_code == 200:
            return response.content
        else:
            print(f"Failed to download image: {url}, status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error downloading image {url}: {e}")
        return None

def resize_image(image_bytes, max_size=(800, 800)):
    """Resize an image to a reasonable size for storage"""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.thumbnail(max_size)
        output = io.BytesIO()
        img.save(output, format='JPEG')
        return output.getvalue()
    except Exception as e:
        print(f"Error resizing image: {e}")
        return None

def generate_random_date(start_date, end_date):
    """Generate a random date between start_date and end_date"""
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    random_date = start_date + timedelta(days=random_number_of_days)
    return random_date

def insert_sample_data():
    """Insert sample data into the database"""
    # Connect to the database
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if we already have items
    cursor.execute("SELECT COUNT(*) FROM items")
    item_count = cursor.fetchone()[0]
    
    if item_count > 10:
        print(f"Database already has {item_count} items. Skipping sample data insertion.")
        conn.close()
        return
    
    # Get the default user_id (should be 1)
    cursor.execute("SELECT user_id FROM users LIMIT 1")
    seller_id = cursor.fetchone()[0]
    
    print(f"Inserting sample data using seller_id: {seller_id}")
    
    # Define date range for item creation (past 3 months to today)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    # Track number of inserted items
    inserted_count = 0
    
    # Insert items from each category
    for category, items in sample_data.items():
        print(f"Adding items for category: {category}")
        
        for item in items:
            # Download and resize the image
            if 'image_url' in item:
                image_bytes = download_image(item['image_url'])
                if image_bytes:
                    image_data = resize_image(image_bytes)
                else:
                    image_data = None
            else:
                image_data = None
            
            # Generate random creation date
            created_at = generate_random_date(start_date, end_date)
            
            # Randomly select status with higher probability for Available
            status = random.choices(
                ["Available", "Pending", "Sold"],
                weights=[0.7, 0.15, 0.15]
            )[0]
            
            # Insert item into database
            insert_query = """
                INSERT INTO items 
                (title, description, price, condition_status, created_at, status, 
                 seller_id, category, contact_preference, location, image_data)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(insert_query, (
                item['title'],
                item['description'],
                item['price'],
                item['condition'],
                created_at,
                status,
                seller_id,
                category,
                item['contact_preference'],
                item['location'],
                image_data
            ))
            
            inserted_count += 1
    
    # Commit the changes
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"Successfully inserted {inserted_count} sample items into the database.")

if __name__ == "__main__":
    insert_sample_data() 
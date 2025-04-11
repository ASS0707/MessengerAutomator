"""
Script to initialize default products in the database.
Run this script to populate the Product table with sample products.
"""

from app import app, db
from models import Product
from datetime import datetime

# Default products for the shop
DEFAULT_PRODUCTS = [
    {
        "name": "Classic T-Shirt",
        "name_ar": "قميص كلاسيكي",
        "description": "A comfortable cotton t-shirt for everyday wear.",
        "description_ar": "قميص قطني مريح للارتداء اليومي.",
        "price": 19.99,
        "category": "Clothing",
        "category_ar": "ملابس",
        "active": True
    },
    {
        "name": "Premium Hoodie",
        "name_ar": "هودي ممتاز",
        "description": "Warm and stylish hoodie for colder days.",
        "description_ar": "هودي دافئ وأنيق للأيام الباردة.",
        "price": 39.99,
        "category": "Clothing",
        "category_ar": "ملابس",
        "active": True
    },
    {
        "name": "Smart Watch",
        "name_ar": "ساعة ذكية",
        "description": "Track your fitness goals and stay connected.",
        "description_ar": "تتبع أهداف لياقتك وابق على اتصال.",
        "price": 129.99,
        "category": "Electronics",
        "category_ar": "إلكترونيات",
        "active": True
    },
    {
        "name": "Wireless Earbuds",
        "name_ar": "سماعات لاسلكية",
        "description": "High-quality sound with noise cancellation.",
        "description_ar": "صوت عالي الجودة مع إلغاء الضوضاء.",
        "price": 79.99,
        "category": "Electronics",
        "category_ar": "إلكترونيات",
        "active": True
    },
    {
        "name": "Leather Wallet",
        "name_ar": "محفظة جلدية",
        "description": "Elegant leather wallet with multiple card slots.",
        "description_ar": "محفظة جلدية أنيقة مع فتحات بطاقات متعددة.",
        "price": 29.99,
        "category": "Accessories",
        "category_ar": "إكسسوارات",
        "active": True
    },
    {
        "name": "Sunglasses",
        "name_ar": "نظارات شمسية",
        "description": "Stylish sunglasses with UV protection.",
        "description_ar": "نظارات شمسية أنيقة مع حماية من الأشعة فوق البنفسجية.",
        "price": 24.99,
        "category": "Accessories",
        "category_ar": "إكسسوارات",
        "active": True
    },
    {
        "name": "Coffee Mug",
        "name_ar": "كوب قهوة",
        "description": "Ceramic mug that keeps your coffee warm.",
        "description_ar": "كوب سيراميك يحافظ على دفء قهوتك.",
        "price": 12.99,
        "category": "Home",
        "category_ar": "المنزل",
        "active": True
    },
    {
        "name": "Scented Candle",
        "name_ar": "شمعة معطرة",
        "description": "Long-lasting scented candle for a cozy atmosphere.",
        "description_ar": "شمعة معطرة طويلة الأمد لأجواء مريحة.",
        "price": 15.99,
        "category": "Home",
        "category_ar": "المنزل",
        "active": True
    }
]

def init_products():
    """Initialize the products in the database"""
    print("Initializing products...")
    
    # Check if products already exist
    existing_count = Product.query.count()
    print(f"Found {existing_count} existing products.")
    
    # Check if our sample products already exist by name
    existing_names = [p.name for p in Product.query.all()]
    
    # Add default products
    added_count = 0
    for product_data in DEFAULT_PRODUCTS:
        # Skip if product with this name already exists
        if product_data["name"] in existing_names:
            print(f"Skipping existing product: {product_data['name']}")
            continue
            
        product = Product(
            name=product_data["name"],
            name_ar=product_data["name_ar"],
            description=product_data["description"],
            description_ar=product_data["description_ar"],
            price=product_data["price"],
            category=product_data["category"],
            category_ar=product_data["category_ar"],
            active=product_data["active"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(product)
        added_count += 1
    
    # Commit changes
    db.session.commit()
    print(f"Added {added_count} new products.")

if __name__ == "__main__":
    with app.app_context():
        init_products()
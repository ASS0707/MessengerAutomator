"""
Script to initialize default bot messages in the database.
Run this script to populate the BotMessage table with default messages.
"""

from app import app, db
from models import BotMessage
from datetime import datetime

# Default messages for the Messenger bot
DEFAULT_MESSAGES = [
    {
        "key": "greeting",
        "en": "Hello! Welcome to our bot. How can I help you today?",
        "ar": "مرحباً! أهلاً بك في روبوتنا. كيف يمكنني مساعدتك اليوم؟"
    },
    {
        "key": "menu",
        "en": "Please select an option:\n- View Products\n- Track Order\n- Contact Support",
        "ar": "الرجاء اختيار خيار:\n- عرض المنتجات\n- تتبع الطلب\n- الاتصال بالدعم"
    },
    {
        "key": "product_categories",
        "en": "Please select a product category:",
        "ar": "الرجاء اختيار فئة المنتج:"
    },
    {
        "key": "product_list",
        "en": "Here are the products in this category:",
        "ar": "إليك المنتجات في هذه الفئة:"
    },
    {
        "key": "order_confirmation",
        "en": "Thank you for your order! Your order ID is [ORDER_ID].",
        "ar": "شكراً لطلبك! رقم طلبك هو [ORDER_ID]."
    },
    {
        "key": "order_details",
        "en": "Please provide your delivery information (name, phone, address):",
        "ar": "يرجى تقديم معلومات التسليم الخاصة بك (الاسم والهاتف والعنوان):"
    },
    {
        "key": "order_success",
        "en": "Your order has been placed successfully! We will contact you soon.",
        "ar": "تم تقديم طلبك بنجاح! سنتصل بك قريباً."
    },
    {
        "key": "order_status",
        "en": "Your order status is: [STATUS]",
        "ar": "حالة طلبك هي: [STATUS]"
    },
    {
        "key": "contact_support",
        "en": "If you need assistance, please contact us at support@example.com",
        "ar": "إذا كنت بحاجة إلى مساعدة، يرجى الاتصال بنا على support@example.com"
    },
    {
        "key": "thank_you",
        "en": "Thank you for shopping with us!",
        "ar": "شكراً للتسوق معنا!"
    }
]

def init_bot_messages():
    """Initialize the bot messages in the database"""
    print("Initializing bot messages...")
    
    # Check if messages already exist
    existing_count = BotMessage.query.count()
    if existing_count > 0:
        print(f"Found {existing_count} existing messages. Skipping initialization.")
        return
    
    # Add default messages
    for message in DEFAULT_MESSAGES:
        bot_message = BotMessage(
            message_key=message["key"],
            message_text=message["en"],
            message_text_ar=message["ar"],
            updated_at=datetime.utcnow()
        )
        db.session.add(bot_message)
    
    # Commit changes
    db.session.commit()
    print(f"Added {len(DEFAULT_MESSAGES)} default bot messages.")

if __name__ == "__main__":
    with app.app_context():
        init_bot_messages()
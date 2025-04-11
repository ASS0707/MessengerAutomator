import json
import logging
import requests
from app import db
from models import (
    Customer, Product, Order, OrderItem, BotMessage, 
    CustomerSession, Setting
)
from datetime import datetime

# Facebook Messenger API endpoint
MESSENGER_API_URL = "https://graph.facebook.com/v16.0/me/messages"
PAGE_ACCESS_TOKEN = "PAGE_ACCESS_TOKEN"  # Should be an environment variable

def send_message(recipient_id, message_data):
    """Send message to recipient via Messenger API"""
    payload = {
        "recipient": {"id": recipient_id},
        "message": message_data
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    params = {
        "access_token": PAGE_ACCESS_TOKEN
    }
    
    try:
        response = requests.post(
            MESSENGER_API_URL,
            params=params,
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            logging.error(f"Failed to send message: {response.text}")
            return False
            
        return True
    except Exception as e:
        logging.error(f"Error sending message: {str(e)}")
        return False

def get_bot_message(key, language='en'):
    """Get bot message text by key and language"""
    message = BotMessage.query.filter_by(message_key=key).first()
    
    if not message:
        # Return a default message if not found
        logging.warning(f"Bot message with key '{key}' not found")
        return f"Message not found: {key}"
    
    return message.message_text_ar if language == 'ar' else message.message_text

def get_user_profile(user_id):
    """Get user profile from Facebook"""
    url = f"https://graph.facebook.com/{user_id}"
    params = {
        "fields": "first_name,last_name,profile_pic",
        "access_token": PAGE_ACCESS_TOKEN
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        return data
    except Exception as e:
        logging.error(f"Error getting user profile: {str(e)}")
        return {}

def get_or_create_customer(messenger_id):
    """Get existing customer or create a new one"""
    customer = Customer.query.filter_by(messenger_id=messenger_id).first()
    
    if not customer:
        # Get user profile from Facebook
        profile = get_user_profile(messenger_id)
        messenger_name = f"{profile.get('first_name', '')} {profile.get('last_name', '')}"
        
        customer = Customer(
            messenger_id=messenger_id,
            messenger_name=messenger_name.strip() or "Facebook User"
        )
        db.session.add(customer)
        db.session.commit()
    
    return customer

def get_or_create_session(messenger_id):
    """Get existing session or create a new one"""
    session = CustomerSession.query.filter_by(messenger_id=messenger_id).first()
    
    if not session:
        session = CustomerSession(messenger_id=messenger_id)
        db.session.add(session)
        db.session.commit()
    
    return session

def send_greeting(recipient_id, language='en'):
    """Send greeting message with menu options"""
    greeting_text = get_bot_message('greeting', language)
    
    # Create quick reply buttons for main menu
    quick_replies = [
        {
            "content_type": "text",
            "title": "Place an Order" if language == 'en' else "طلب جديد",
            "payload": "PLACE_ORDER"
        },
        {
            "content_type": "text",
            "title": "View Prices" if language == 'en' else "عرض الأسعار",
            "payload": "VIEW_PRICES"
        },
        {
            "content_type": "text",
            "title": "Customer Support" if language == 'en' else "خدمة العملاء",
            "payload": "CUSTOMER_SUPPORT"
        }
    ]
    
    message_data = {
        "text": greeting_text,
        "quick_replies": quick_replies
    }
    
    return send_message(recipient_id, message_data)

def send_product_categories(recipient_id, language='en'):
    """Send product categories to user"""
    # Get unique categories from the database
    categories = db.session.query(Product.category, Product.category_ar).distinct().all()
    
    if not categories:
        message = get_bot_message('no_products', language)
        return send_message(recipient_id, {"text": message})
    
    category_message = get_bot_message('view_categories', language)
    
    # Create buttons for each category
    quick_replies = []
    for category, category_ar in categories:
        quick_replies.append({
            "content_type": "text",
            "title": category_ar if language == 'ar' else category,
            "payload": f"CATEGORY_{category}"
        })
    
    # Add a back button
    quick_replies.append({
        "content_type": "text",
        "title": "Main Menu" if language == 'en' else "القائمة الرئيسية",
        "payload": "BACK_TO_MENU"
    })
    
    message_data = {
        "text": category_message,
        "quick_replies": quick_replies
    }
    
    return send_message(recipient_id, message_data)

def send_products_by_category(recipient_id, category, language='en'):
    """Send products in a specific category"""
    products = Product.query.filter_by(category=category, active=True).all()
    
    if not products:
        message = get_bot_message('no_products_in_category', language)
        return send_message(recipient_id, {"text": message})
    
    products_message = get_bot_message('select_product', language)
    
    elements = []
    for product in products:
        name = product.name_ar if language == 'ar' else product.name
        description = product.description_ar if language == 'ar' else product.description
        
        element = {
            "title": name,
            "subtitle": f"{description}\nPrice: {product.price}",
            "buttons": [
                {
                    "type": "postback",
                    "title": "Order Now" if language == 'en' else "اطلب الآن",
                    "payload": f"ORDER_PRODUCT_{product.id}"
                }
            ]
        }
        elements.append(element)
    
    message_data = {
        "attachment": {
            "type": "template",
            "payload": {
                "template_type": "generic",
                "elements": elements
            }
        }
    }
    
    return send_message(recipient_id, message_data)

def start_order_process(recipient_id, product_id, language='en'):
    """Start the order process for a specific product"""
    product = Product.query.get(product_id)
    
    if not product:
        message = get_bot_message('product_not_found', language)
        return send_message(recipient_id, {"text": message})
    
    # Update session
    session = get_or_create_session(recipient_id)
    session.state = 'collecting_name'
    session_data = {
        'product_id': product_id,
        'language': language
    }
    session.set_data(session_data)
    db.session.commit()
    
    # Ask for customer name
    name_request = get_bot_message('ask_name', language)
    
    # Get the customer object
    customer = get_or_create_customer(recipient_id)
    
    # If we already have the name, pre-fill it
    if customer.full_name:
        name_request += f"\n{customer.full_name}"
    
    return send_message(recipient_id, {"text": name_request})

def process_order_input(recipient_id, message_text):
    """Process order input based on current session state"""
    session = get_or_create_session(recipient_id)
    session_data = session.get_data()
    language = session_data.get('language', 'en')
    
    customer = get_or_create_customer(recipient_id)
    
    if session.state == 'collecting_name':
        # Store the name
        customer.full_name = message_text
        db.session.commit()
        
        # Move to next state - collecting phone
        session.state = 'collecting_phone'
        db.session.commit()
        
        # Ask for phone number
        phone_request = get_bot_message('ask_phone', language)
        
        # If we already have the phone, pre-fill it
        if customer.phone:
            phone_request += f"\n{customer.phone}"
            
        return send_message(recipient_id, {"text": phone_request})
    
    elif session.state == 'collecting_phone':
        # Store the phone
        customer.phone = message_text
        db.session.commit()
        
        # Move to next state - collecting address
        session.state = 'collecting_address'
        db.session.commit()
        
        # Ask for address
        address_request = get_bot_message('ask_address', language)
        
        # If we already have the address, pre-fill it
        if customer.address:
            address_request += f"\n{customer.address}"
            
        return send_message(recipient_id, {"text": address_request})
    
    elif session.state == 'collecting_address':
        # Store the address
        customer.address = message_text
        db.session.commit()
        
        # Move to next state - collecting notes
        session.state = 'collecting_notes'
        db.session.commit()
        
        # Ask for notes
        notes_request = get_bot_message('ask_notes', language)
        return send_message(recipient_id, {"text": notes_request})
    
    elif session.state == 'collecting_notes':
        # Create the order
        product_id = session_data.get('product_id')
        product = Product.query.get(product_id)
        
        if not product:
            message = get_bot_message('product_not_found', language)
            return send_message(recipient_id, {"text": message})
        
        # Create order
        order = Order(
            customer_id=customer.id,
            notes=message_text,
            total_amount=product.price
        )
        db.session.add(order)
        db.session.flush()  # Get the order ID without committing yet
        
        # Create order item
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=1,
            price=product.price
        )
        db.session.add(order_item)
        db.session.commit()
        
        # Reset session
        session.state = 'start'
        session.set_data({})
        db.session.commit()
        
        # Send order confirmation
        confirm_message = get_bot_message('order_confirmation', language)
        confirm_message = confirm_message.replace('[ORDER_ID]', str(order.id))
        confirm_message = confirm_message.replace('[PRODUCT]', product.name_ar if language == 'ar' else product.name)
        confirm_message = confirm_message.replace('[PRICE]', str(product.price))
        
        # Send the confirmation message
        send_message(recipient_id, {"text": confirm_message})
        
        # Offer to go back to main menu
        quick_replies = [
            {
                "content_type": "text",
                "title": "Main Menu" if language == 'en' else "القائمة الرئيسية",
                "payload": "BACK_TO_MENU"
            }
        ]
        
        thank_you = get_bot_message('thank_you', language)
        return send_message(recipient_id, {
            "text": thank_you,
            "quick_replies": quick_replies
        })
    
    else:
        # Unknown state - reset to start
        session.state = 'start'
        session.set_data({})
        db.session.commit()
        
        return send_greeting(recipient_id, language)

def handle_bot_message(sender_id, messaging_event, payload=None):
    """Handle incoming messages and postbacks from users"""
    # Get or create customer
    customer = get_or_create_customer(sender_id)
    
    # Get or create session
    session = get_or_create_session(sender_id)
    session_data = session.get_data()
    language = session_data.get('language', 'en')  # Default to English
    
    # Handle postback (button clicks)
    if payload:
        if payload == "PLACE_ORDER":
            return send_product_categories(sender_id, language)
        
        elif payload == "VIEW_PRICES":
            return send_product_categories(sender_id, language)
        
        elif payload == "CUSTOMER_SUPPORT":
            support_message = get_bot_message('customer_support', language)
            return send_message(sender_id, {"text": support_message})
        
        elif payload == "BACK_TO_MENU":
            session.state = 'start'
            session.set_data({})
            db.session.commit()
            return send_greeting(sender_id, language)
        
        elif payload.startswith("CATEGORY_"):
            category = payload.replace("CATEGORY_", "")
            return send_products_by_category(sender_id, category, language)
        
        elif payload.startswith("ORDER_PRODUCT_"):
            product_id = int(payload.replace("ORDER_PRODUCT_", ""))
            return start_order_process(sender_id, product_id, language)
    
    # Handle text messages
    elif messaging_event.get('message', {}).get('text'):
        message_text = messaging_event.get('message', {}).get('text')
        
        # Check if this is part of an ongoing order process
        if session.state != 'start':
            return process_order_input(sender_id, message_text)
        
        # Handle language change
        if message_text.lower() in ['arabic', 'العربية']:
            session_data['language'] = 'ar'
            session.set_data(session_data)
            db.session.commit()
            return send_greeting(sender_id, 'ar')
        
        if message_text.lower() in ['english', 'الإنجليزية']:
            session_data['language'] = 'en'
            session.set_data(session_data)
            db.session.commit()
            return send_greeting(sender_id, 'en')
        
        # Handle quick reply payloads
        if messaging_event.get('message', {}).get('quick_reply', {}).get('payload'):
            payload = messaging_event.get('message', {}).get('quick_reply', {}).get('payload')
            return handle_bot_message(sender_id, messaging_event, payload)
        
        # Default to greeting for any other message
        return send_greeting(sender_id, language)
    
    # Default response
    return {"success": True}

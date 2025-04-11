from flask import jsonify, request, render_template, redirect, url_for, flash
from app import app, db
from models import Customer, Product, Order, OrderItem, BotMessage, CustomerSession
from flask_login import login_required
import json
import logging
from bot_handler import handle_bot_message

@app.route('/')
def index():
    """Render the main landing page"""
    return render_template('login.html')

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    """Verify the webhook with Facebook Messenger Platform"""
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    verify_token = "MESSENGER_VERIFY_TOKEN"  # Should be set as an environment variable
    
    if mode and token:
        if mode == 'subscribe' and token == verify_token:
            logging.info("Webhook verified!")
            return challenge
        else:
            return jsonify({"success": False}), 403
    
    return jsonify({"success": False}), 400

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming messages from Messenger"""
    data = request.json
    logging.debug(f"Received webhook data: {data}")
    
    if data.get('object') == 'page':
        for entry in data.get('entry', []):
            for messaging_event in entry.get('messaging', []):
                sender_id = messaging_event.get('sender', {}).get('id')
                
                # Check if this is a message event
                if messaging_event.get('message'):
                    # Process the message
                    response = handle_bot_message(sender_id, messaging_event)
                    return jsonify(response)
                
                # Check if this is a postback event (button click)
                if messaging_event.get('postback'):
                    # Process postback
                    payload = messaging_event.get('postback', {}).get('payload')
                    response = handle_bot_message(sender_id, messaging_event, payload=payload)
                    return jsonify(response)
                
    return jsonify({"success": True})

@app.route('/webhook/send', methods=['POST'])
def send_message():
    """Test endpoint to send a message to a user"""
    data = request.json
    recipient_id = data.get('recipient_id')
    message = data.get('message')
    
    if not recipient_id or not message:
        return jsonify({"error": "Missing recipient_id or message"}), 400
    
    # Here you would call your send message function
    # This is a placeholder response
    return jsonify({"success": True, "message": "Message sent"})

@app.route('/order-status/<order_id>')
def order_status(order_id):
    """Public order status page for customers to track their orders"""
    order = Order.query.get_or_404(order_id)
    customer = Customer.query.get(order.customer_id)
    
    return render_template(
        'order_status.html', 
        order=order,
        customer=customer,
        items=order.items
    )

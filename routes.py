from flask import jsonify, request, render_template, redirect, url_for, flash
from app import app, db, logger
from models import Customer, Product, Order, OrderItem, BotMessage, CustomerSession
from flask_login import login_required, current_user
import json
import logging
import traceback
from datetime import datetime
from bot_handler import handle_bot_message

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    logger.error(f"404 Error: {request.path}")
    return render_template('error.html', error_code=404, message="Page not found"), 404

@app.errorhandler(500)
def internal_server_error(e):
    logger.error(f"500 Error: {traceback.format_exc()}")
    return render_template('error.html', error_code=500, message="Internal server error"), 500

# Add context processor to provide variables to all templates
@app.context_processor
def inject_user():
    return dict(
        now=datetime.now(),
        rtl=False  # Default to LTR, can be changed in settings
    )

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
    
    # Get verify token from settings if available
    from models import Setting
    verify_token = Setting.get('verify_token', "")
    
    if mode and token:
        if mode == 'subscribe' and token == verify_token:
            logging.info("Webhook verified!")
            return challenge
        else:
            logging.warning(f"Failed webhook verification: Invalid token or mode. Mode: {mode}, Token: {token}")
            return jsonify({"success": False, "error": "Invalid verification token"}), 403
    
    logging.warning("Failed webhook verification: Missing mode or token")
    return jsonify({"success": False, "error": "Missing hub.mode or hub.verify_token"}), 400

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming messages from Messenger"""
    try:
        # Check if we have a valid JSON payload
        if not request.is_json:
            logging.warning("Received webhook with invalid content type")
            return jsonify({"success": False, "error": "Invalid content type"}), 400
        
        data = request.json
        logging.debug(f"Received webhook data: {data}")
        
        if data.get('object') == 'page':
            for entry in data.get('entry', []):
                for messaging_event in entry.get('messaging', []):
                    sender_id = messaging_event.get('sender', {}).get('id')
                    
                    if not sender_id:
                        logging.warning("Received messaging event with no sender ID")
                        continue
                    
                    # Check if this is a message event
                    if messaging_event.get('message'):
                        # Process the message
                        logging.info(f"Processing message from sender: {sender_id}")
                        response = handle_bot_message(sender_id, messaging_event)
                        return jsonify(response)
                    
                    # Check if this is a postback event (button click)
                    if messaging_event.get('postback'):
                        # Process postback
                        payload = messaging_event.get('postback', {}).get('payload')
                        logging.info(f"Processing postback from sender: {sender_id}, payload: {payload}")
                        response = handle_bot_message(sender_id, messaging_event, payload=payload)
                        return jsonify(response)
        
        # Return success even if we didn't process anything to acknowledge receipt
        return jsonify({"success": True})
        
    except Exception as e:
        logging.error(f"Error processing webhook: {str(e)}")
        return jsonify({"success": False, "error": "Server error"}), 500

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

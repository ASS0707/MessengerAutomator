from app import db
from flask_login import UserMixin
from datetime import datetime
import json

class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Admin {self.username}>'

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    messenger_id = db.Column(db.String(100), unique=True, nullable=False)
    messenger_name = db.Column(db.String(100))
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    orders = db.relationship('Order', backref='customer', lazy=True)
    
    def __repr__(self):
        return f'<Customer {self.full_name if self.full_name else self.messenger_name}>'

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    name_ar = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    description_ar = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50))
    category_ar = db.Column(db.String(50))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    orders = db.relationship('OrderItem', backref='product', lazy=True)
    
    def __repr__(self):
        return f'<Product {self.name}>'

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    status = db.Column(db.String(20), default='new')  # new, processing, shipped, delivered, cancelled
    notes = db.Column(db.Text)
    admin_notes = db.Column(db.Text)
    total_amount = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Order {self.id}>'

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    price = db.Column(db.Float, nullable=False)  # Price at the time of purchase
    
    def __repr__(self):
        return f'<OrderItem {self.id}>'

class BotMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message_key = db.Column(db.String(50), unique=True, nullable=False)
    message_text = db.Column(db.Text, nullable=False)
    message_text_ar = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<BotMessage {self.message_key}>'

class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text)
    
    @classmethod
    def get(cls, key, default=None):
        setting = cls.query.filter_by(key=key).first()
        if setting:
            try:
                # Try to parse as JSON if it's a JSON string
                return json.loads(setting.value)
            except:
                return setting.value
        return default
    
    @classmethod
    def set(cls, key, value):
        setting = cls.query.filter_by(key=key).first()
        
        # Convert dict/list to JSON string
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
            
        if setting:
            setting.value = value
        else:
            setting = cls(key=key, value=value)
            db.session.add(setting)
        
        db.session.commit()
        return setting

class CustomerSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    messenger_id = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(50), default='start')
    data = db.Column(db.Text)  # JSON serialized session data
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_data(self):
        if self.data:
            return json.loads(self.data)
        return {}
    
    def set_data(self, data_dict):
        self.data = json.dumps(data_dict)
        
    def update_data(self, new_data):
        data = self.get_data()
        data.update(new_data)
        self.set_data(data)

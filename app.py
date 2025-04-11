import os
import logging
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager

# Configure logging - write to stderr for easier debugging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Define SQLAlchemy base
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)
app.debug = True  # Enable Flask debugging
app.secret_key = os.environ.get("SESSION_SECRET", "messenger-bot-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///messenger_bot.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database with the app
db.init_app(app)

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

from models import Admin

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

# Create all database tables
with app.app_context():
    import models
    db.create_all()
    
    # Create default admin if doesn't exist
    if not Admin.query.filter_by(username='admin').first():
        from werkzeug.security import generate_password_hash
        admin = Admin(
            username='admin',
            password_hash=generate_password_hash('admin123'),
            email='admin@example.com',
            name='Administrator'
        )
        db.session.add(admin)
        db.session.commit()
        logging.info("Default admin user created")

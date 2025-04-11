import os

class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('SESSION_SECRET', 'messenger-bot-default-key')
    DEBUG = True
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///messenger_bot.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Facebook Messenger configuration
    MESSENGER_PAGE_ACCESS_TOKEN = os.environ.get('PAGE_ACCESS_TOKEN', '')
    MESSENGER_VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN', 'MESSENGER_VERIFY_TOKEN')
    
    # Backup configuration
    BACKUP_DIRECTORY = 'backups'
    
    # Business information (defaults, will be overridden by database settings)
    DEFAULT_BUSINESS_NAME = 'My Business'
    DEFAULT_BUSINESS_EMAIL = 'contact@example.com'
    
    # Pagination settings
    ITEMS_PER_PAGE = 20

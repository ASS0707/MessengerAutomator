from app import app
import routes
import admin_routes
import bot_handler
from init_bot_messages import init_bot_messages

if __name__ == "__main__":
    with app.app_context():
        init_bot_messages()
    app.run(host="0.0.0.0", port=5000, debug=True)

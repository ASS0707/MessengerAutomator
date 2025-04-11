from app import app
import routes
import admin_routes
import bot_handler

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

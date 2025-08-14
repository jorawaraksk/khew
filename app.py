import os
import threading
from flask import Flask
from main import main  # Your Telegram bot main() function

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!", 200

def run_flask():
    # Use Render's PORT if available, otherwise fallback to 8000
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    # Start Flask in a background thread
    threading.Thread(target=run_flask).start()

    # Start Telegram bot safely with error handling
    try:
        print("Starting Telegram bot...")
        main()
    except Exception as e:
        print("Bot failed to start!")
        print(str(e))

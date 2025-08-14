import os
import threading
from flask import Flask
from main import main  # Import your bot main function

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Running!", 200

def run_flask():
    # Auto-detect port from Render environment or default to 10000
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    # Run Flask in a separate thread
    threading.Thread(target=run_flask).start()
    # Start the Telegram bot
    main()

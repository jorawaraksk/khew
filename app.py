import os
from flask import Flask
import threading
from main import main

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Running!", 200

import os

def run_flask():
    port = int(os.environ.get("PORT", 8000))  # use Render's assigned port
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    main()

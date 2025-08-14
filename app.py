from flask import Flask
import threading
from main import main  # import your Telegram bot main function

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Running!", 200

def run_flask():
    app.run(host='0.0.0.0', port=8000)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    main()

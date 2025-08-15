from flask import Flask
import threading
import main  # Import your bot script

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_bot():
    main.run()  # Make sure your main.py has a run() function to start the bot

if __name__ == '__main__':
    # Start bot in a separate thread
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    # Run Flask server
    app.run(host='0.0.0.0', port=10000)

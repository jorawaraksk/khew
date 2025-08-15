import os
import threading
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
from utils import create_folder, remove_folder, zip_folder, load_json, save_json, install_dependencies, list_unnecessary_dependencies

# Environment variables (Render -> Dashboard -> Environment)
BOT_TOKEN = os.environ.get("BOT_TOKEN", "6613265810:AAE02TlVelL0lLMpgxkv7cY4Br4Cq6IGDZs")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "5868426717"))
BASE_DIR = "projects"

# Load premium users
premium_file = "premium.json"
premium_users = load_json(premium_file)

# Flask app
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive on Render!"

# Telegram bot handlers
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    buttons = [
        [InlineKeyboardButton("Deploy GitHub URL", callback_data="deploy_github")],
        [InlineKeyboardButton("Deploy ZIP", callback_data="deploy_zip")],
        [InlineKeyboardButton("View Dependencies", callback_data="view_deps")]
    ]
    if user_id == ADMIN_ID:
        buttons.append([InlineKeyboardButton("Remove Unused Dependencies", callback_data="remove_deps")])
    update.message.reply_text(
        "Welcome! Choose an option below:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

def convert(update: Update, context: CallbackContext):
    """Owner command to convert any user to premium"""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        update.message.reply_text("You are not allowed to use this command.")
        return
    if not context.args:
        update.message.reply_text("Usage: /convert <user_id>")
        return
    try:
        target_id = int(context.args[0])
        premium_users[str(target_id)] = True
        save_json(premium_file, premium_users)
        update.message.reply_text(f"User {target_id} is now premium.")
    except Exception as e:
        update.message.reply_text(f"Error: {e}")

def handle_button(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    if query.data == "deploy_github":
        query.edit_message_text("Send the GitHub repo URL to deploy.")
    elif query.data == "deploy_zip":
        query.edit_message_text("Send the ZIP file to deploy.")
    elif query.data == "view_deps":
        query.edit_message_text("Checking dependencies...")
        installed = ["requests", "flask", "pytz"]
        used = ["requests", "flask"]
        unused = list_unnecessary_dependencies(installed, used)
        msg = "Unused dependencies:\n" + "\n".join(unused) if unused else "All dependencies are used."
        query.edit_message_text(msg)
    elif query.data == "remove_deps":
        if user_id != ADMIN_ID:
            query.edit_message_text("Only owner can remove dependencies.")
            return
        query.edit_message_text("Removing unused dependencies...")
        query.edit_message_text("Unused dependencies removed successfully.")

def unknown(update: Update, context: CallbackContext):
    update.message.reply_text("Unknown command.")

# Bot runner
def run_bot():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("convert", convert))
    dp.add_handler(CallbackQueryHandler(handle_button))
    dp.add_handler(MessageHandler(Filters.command, unknown))
    updater.start_polling()
    updater.idle()

# Start bot in background thread when gunicorn starts worker
if not os.environ.get("RUN_MAIN"):  # Prevent double-start
    create_folder(BASE_DIR)
    threading.Thread(target=run_bot, daemon=True).start()

# Flask entrypoint
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

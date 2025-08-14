import os
import subprocess
import threading
import json
import shutil
from zipfile import ZipFile
from urllib.parse import urlparse
from datetime import datetime, timedelta, timezone as dt_timezone

from pytz import timezone
from apscheduler.schedulers.background import BackgroundScheduler

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
    CallbackContext,
)

BOT_TOKEN = "6613265810:AAE02TlVelL0lLMpgxkv7cY4Br4Cq6IGDZs"
ADMIN_ID = "5868426717"

BASE_DIR = "projects"
LOG_DIR = "logs"
PREMIUM_FILE = "premium.json"
MAX_FILE_SIZE = 50 * 1024 * 1024

os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

user_projects = {}
premium_users = {}

scheduler = BackgroundScheduler(timezone=timezone("Asia/Kolkata"))
scheduler.start()


# ----------------- Premium Handling -----------------
def load_premium():
    if os.path.exists(PREMIUM_FILE):
        with open(PREMIUM_FILE, "r") as f:
            return json.load(f)
    return {}


def save_premium(data):
    with open(PREMIUM_FILE, "w") as f:
        json.dump(data, f)


premium_users = load_premium()


def is_premium(uid):
    expiry = premium_users.get(str(uid))
    if not expiry:
        return False
    expiry_dt = datetime.strptime(
        expiry, "%Y-%m-%d %H:%M:%S"
    ).replace(tzinfo=dt_timezone.utc)
    if datetime.now(dt_timezone.utc) > expiry_dt:
        del premium_users[str(uid)]
        save_premium(premium_users)
        return False
    return True


# ----------------- Run / Stop Projects -----------------
def stop_project(uid, filename, bot=None):
    proc = user_projects.get(uid, {}).get(filename)
    if proc:
        proc.kill()
        user_projects[uid].pop(filename, None)
        if bot:
            bot.send_message(
                chat_id=uid,
                text=f"💤 Project <b>{filename}</b> auto-terminated.",
                parse_mode="HTML",
            )


def run_command(uid, command, display_name, update, context):
    logpath = os.path.join(LOG_DIR, f"{uid}_{display_name}.txt")

    def execute():
        with open(logpath, "w") as log_file:
            proc = subprocess.Popen(
                command, shell=True, stdout=log_file, stderr=subprocess.STDOUT
            )
            user_projects.setdefault(uid, {})
            user_projects[uid][display_name] = proc

            if not is_premium(uid):
                scheduler.add_job(
                    stop_project,
                    "date",
                    run_date=datetime.now(dt_timezone.utc) + timedelta(minutes=10),
                    args=[uid, display_name, context.bot],
                )

    threading.Thread(target=execute).start()

    update.effective_message.reply_text(
        f"✅ Project <b>{display_name}</b> started.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🛑 Stop", callback_data=f"terminate_{display_name}"),
                    InlineKeyboardButton("🔁 Restart", callback_data=f"restart_{display_name}"),
                    InlineKeyboardButton("📜 Log", callback_data=f"log_{display_name}"),
                ]
            ]
        ),
    )


# ----------------- Telegram Commands -----------------
def start(update: Update, context: CallbackContext):
    uid = update.effective_user.id
    name = update.effective_user.first_name
    image = "https://files.catbox.moe/efem5j.jpg"

    keyboard = [
        [InlineKeyboardButton("🐍 Host Python File", callback_data="host_py")],
        [InlineKeyboardButton("📁 My Projects", callback_data="my_projects")],
        [InlineKeyboardButton("🛠 Terminal a Project", callback_data="terminate_one")],
        [InlineKeyboardButton("⛔ Terminate All", callback_data="terminate_all")],
        [InlineKeyboardButton("📜 My Plan", callback_data="my_plan")],
        [InlineKeyboardButton("🧬 Deploy GitHub URL", callback_data="deploy_github")],
        [InlineKeyboardButton("🗜 Deploy ZIP File", callback_data="deploy_zip")],
    ]

    caption = f"""👋 Hello <b>{name}</b>,

💐 Welcome to ⛥ PLAY-Z PYTHON HOSTING BOT ⛥
🔷 Host your Python codes easily
🚀 Deploy up to 3 .py files (unlimited for premium)
⏱️ 10-min Auto Sleep
📜 Smart Logs | 🧠 Auto Command

<em>© Powered by PLAY-Z HACKING</em>"""

    context.bot.send_photo(
        chat_id=uid,
        photo=image,
        caption=caption,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ----------------- Button Handler -----------------
def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    uid = query.from_user.id
    data = query.data

    if data.startswith("terminate_"):
        filename = data.split("terminate_")[1]
        stop_project(uid, filename, context.bot)
        query.message.reply_text(f"✅ Project <b>{filename}</b> terminated.", parse_mode="HTML")

    elif data.startswith("restart_"):
        filename = data.split("restart_")[1]
        path = None
        for f in os.listdir(BASE_DIR):
            full_path = os.path.join(BASE_DIR, f, filename)
            if os.path.exists(full_path):
                path = full_path
                break
        if path:
            run_command(uid, f"python3 '{path}'", filename, update, context)
        else:
            query.message.reply_text("❌ File not found.")

    elif data.startswith("log_"):
        filename = data.split("log_")[1]
        logpath = os.path.join(LOG_DIR, f"{uid}_{filename}.txt")
        if os.path.exists(logpath):
            with open(logpath, "rb") as f:
                context.bot.send_document(chat_id=uid, document=f, filename=f"{filename}.log")
        else:
            context.bot.send_message(chat_id=uid, text="❌ Log not found.")

    elif data.startswith("runzip_") or data.startswith("rungit_"):
        _, file_uid, filename = data.split("_", 2)
        file_uid = int(file_uid)
        full_path = None
        for f in os.listdir(BASE_DIR):
            folder_path = os.path.join(BASE_DIR, f)
            if f.startswith(f"{file_uid}_") and os.path.exists(os.path.join(folder_path, filename)):
                full_path = os.path.join(folder_path, filename)
                break
        if not full_path:
            return query.message.reply_text("❌ File not found.")
        run_command(file_uid, f"python3 '{full_path}'", filename, update, context)
        query.message.reply_text(f"✅ Project <b>{filename}</b> started.", parse_mode="HTML")


# ----------------- Handle Python File -----------------
def handle_file(update: Update, context: CallbackContext):
    file = update.message.document
    uid = update.effective_user.id
    if not file.file_name.endswith(".py"):
        return update.message.reply_text("❌ Send a valid .py file only.")
    if file.file_size > MAX_FILE_SIZE:
        return update.message.reply_text("❌ File too large. Max 50MB allowed.")
    filename = file.file_name
    path = os.path.join(BASE_DIR, filename)
    file.get_file().download(path)
    run_command(uid, f"python3 '{path}'", filename, update, context)


# ----------------- Handle ZIP -----------------
def handle_zip(update: Update, context: CallbackContext):
    file = update.message.document
    uid = update.effective_user.id
    if not file.file_name.endswith(".zip"):
        return update.message.reply_text("❌ Send a valid .zip file.")
    if file.file_size > MAX_FILE_SIZE:
        return update.message.reply_text("❌ ZIP too large. Max 50MB allowed.")

    zip_path = os.path.join(BASE_DIR, file.file_name)
    file.get_file().download(zip_path)
    extract_dir = os.path.join(BASE_DIR, f"{uid}_{file.file_name[:-4]}")
    os.makedirs(extract_dir, exist_ok=True)

    try:
        with ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)
        py_files = [f for f in os.listdir(extract_dir) if f.endswith(".py")]
        if not py_files:
            return update.message.reply_text("❌ No Python files found in ZIP.")

        if len(py_files) == 1:
            run_command(uid, f"python3 '{os.path.join(extract_dir, py_files[0])}'", py_files[0], update, context)
            update.message.reply_text(
                f"✅ Project <b>{py_files[0]}</b> started automatically.", parse_mode="HTML"
            )
        else:
            buttons = [[InlineKeyboardButton(f"🛠 Run {f}", callback_data=f"runzip_{uid}_{f}")] for f in py_files]
            update.message.reply_text("Select Python file to run:", reply_markup=InlineKeyboardMarkup(buttons))

    except Exception as e:
        update.message.reply_text(f"❌ Failed to extract/run ZIP.\nError: {e}")


# ----------------- Handle GitHub -----------------
def handle_github(update: Update, context: CallbackContext):
    uid = update.effective_user.id
    text = update.message.text.strip()
    if not text.startswith("https://github.com/"):
        return update.message.reply_text("❌ Send a valid GitHub repo link.")

    repo_name = urlparse(text).path.strip("/").split("/")[-1]
    clone_dir = os.path.join(BASE_DIR, f"{uid}_{repo_name}")

    try:
        if os.path.exists(clone_dir):
            shutil.rmtree(clone_dir)
        subprocess.check_call(f"git clone '{text}' '{clone_dir}'", shell=True)

        py_files = [f for f in os.listdir(clone_dir) if f.endswith(".py")]
        if not py_files:
            return update.message.reply_text("❌ No Python files found in repo.")

        if len(py_files) == 1:
            run_command(uid, f"python3 '{os.path.join(clone_dir, py_files[0])}'", py_files[0], update, context)
            update.message.reply_text(
                f"✅ Project <b>{py_files[0]}</b> started automatically.", parse_mode="HTML"
            )
        else:
            buttons = [[InlineKeyboardButton(f"🛠 Run {f}", callback_data=f"rungit_{uid}_{f}")] for f in py_files]
            update.message.reply_text("Select Python file to run:", reply_markup=InlineKeyboardMarkup(buttons))

    except Exception as e:
        update.message.reply_text(f"❌ Failed to clone/run repo.\nError: {e}")


# ----------------- Add Premium -----------------
def add_premium(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        return update.message.reply_text("❌ Only admin can use this.")
    try:
        uid = str(context.args[0])
        days = int(context.args[1])
        expiry = (datetime.now(dt_timezone.utc) + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        premium_users[uid] = expiry
        save_premium(premium_users)
        update.message.reply_text(f"✅ Premium activated for {uid} ({days} days)")
    except:
        update.message.reply_text("❌ Usage: /add <user_id> <days>")


# ----------------- Main -----------------
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("add", add_premium, pass_args=True))
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(MessageHandler(Filters.document.mime_type("text/x-python"), handle_file))
    dp.add_handler(MessageHandler(Filters.document.mime_type("application/zip"), handle_zip))
    dp.add_handler(MessageHandler(Filters.text & (~Filters.command), handle_github))

    updater.start_polling()
    updater.idle()

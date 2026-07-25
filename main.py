"""
SOIKOT HOSTING — Telegram Bot & Web App Template
python-telegram-bot v20 + Flask | Ready to Deploy
Monitor 404 error ঠিক করা হয়েছে
"""

import asyncio
import logging
import time
import threading
import requests
import os
from flask import Flask, render_template, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ==========================================
# কনফিগারেশন (এখানে আপনার তথ্য দিন)
# ==========================================
TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
# হোস্টিং URL (যেমন: https://soikot-hosting.onrender.com)
# খালি রাখলে লোকালহোস্ট ব্যবহার করবে
HOSTING_URL = os.getenv("HOSTING_URL", "http://localhost:5000") 

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("werkzeug").setLevel(logging.WARNING) # Flask লগ চুপ রাখা
logger = logging.getLogger(__name__)

start_time = time.time()

# ==========================================
# Flask Web Server (Web App হোস্ট করার জন্য)
# ==========================================
flask_app = Flask(__name__)

@flask_app.route('/')
def webapp_home():
    """Telegram Web App এর মেইন পেজ"""
    return render_template('index.html')

@flask_app.route('/api/monitor')
def monitor():
    """Keep-alive monitor এর জন্য এন্ডপয়েন্ট"""
    uptime = time.time() - start_time
    return jsonify({"status": "ok", "uptime": uptime})

def run_flask():
    """Flask সার্ভার আলাদা থ্রেডে চালানো"""
    port = int(os.getenv("PORT", 5000))
    flask_app.run(host='0.0.0.0', port=port, use_reloader=False)

# ==========================================
# Telegram Bot Handlers
# ==========================================
def keep_alive_monitor(url: str, interval: int = 30):
    monitor_url = f"{url.rstrip('/')}/api/monitor"
    while True:
        try:
            resp = requests.get(monitor_url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                logger.info(f"✅ Monitor OK — uptime: {data.get('uptime', 0):.0f}s")
            else:
                logger.warning(f"⚠ Monitor: HTTP {resp.status_code}")
        except Exception as e:
            logger.warning(f"⚠ Monitor: {e}")
        time.sleep(interval)

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Web App খোলার বাটন তৈরি
    keyboard = [
        [InlineKeyboardButton("🌐 ওয়েব অ্যাপ খুলুন", web_app=WebAppInfo(url=HOSTING_URL))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"👋 আস্সালামু আলাইকুম, {user.first_name}!\n\n"
        "✅ আমি SOIKOT HOSTING APP-এ চলছি!\n"
        "⚡ python-telegram-bot v20 + Flask Web App\n\n"
        "নিচের বাটনে ক্লিক করে ওয়েব অ্যাপটি ব্যবহার করুন:",
        reply_markup=reply_markup
    )

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🆘 <b>Help Menu</b>\n\n"
        "/start — Bot ও Web App চালু করুন\n"
        "/ping  — Bot জীবিত আছে কিনা দেখুন\n"
        "/help  — এই মেনু দেখুন",
        parse_mode="HTML",
    )

async def cmd_ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🏓 Pong! আমি চালু আছি ✅\nUptime: {int(time.time() - start_time)}s")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🔁 Echo: {update.message.text}")

# ==========================================
# Main Execution
# ==========================================
def main():
    logger.info("🚀 SOIKOT HOSTING Bot & Web App শুরু হচ্ছে...")

    # ১. Flask Web Server থ্রেড শুরু করা
    threading.Thread(target=run_flask, daemon=True, name="flask_server").start()
    logger.info(f"🌐 Web App চলছে: {HOSTING_URL}")

    # ২. Keep-alive Monitor শুরু করা
    if HOSTING_URL and "localhost" not in HOSTING_URL:
        threading.Thread(
            target=keep_alive_monitor,
            args=(HOSTING_URL, 30),
            daemon=True,
            name="monitor",
        ).start()
        logger.info(f"🔍 Monitor চালু: {HOSTING_URL}/api/monitor")
    else:
        logger.info("ℹ Monitor বন্ধ (লোকাল ডেভেলপমেন্ট মোড)")

    # ৩. Telegram Bot সেটআপ
    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .connection_pool_size(8)
        .connect_timeout(15)
        .read_timeout(30)
        .write_timeout(15)
        .build()
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("ping", cmd_ping))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("✅ Bot polling started!")
    app.run_polling(poll_interval=0, timeout=30, drop_pending_updates=True)

if __name__ == "__main__":
    main()
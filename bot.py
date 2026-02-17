import os
import logging
import asyncio
from threading import Thread
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ForceReply
)
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)
from flask import Flask

# ================== تنظیمات ==================
BOT_TOKEN = "8308402050:AAEAKeF2jcsoVmAZok6aLvOAfuiLzPv10gE"
ADMIN_ID = 5918934605
# ============================================

# تنظیم لاگینگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

blocked_users = set()
pending_replies = {}

# --------- وب‌سرور Flask برای Koyeb ---------
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "ربات فعال است"

@app_flask.route('/health')
def health():
    return "OK", 200

def run_flask():
    port = int(os.environ.get("PORT", 8000))
    app_flask.run(host='0.0.0.0', port=port)
# --------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"User {user.id} started the bot")
    
    if user.id in blocked_users:
        await update.message.reply_text("شما مسدود شده‌اید.")
        return
    
    await update.message.reply_text(
        "سلام ❤️.\n"
        "پیام ناشناسی که میخوای بفرستی رو اینجا تایپ کن"
    )

async def user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if user.id == ADMIN_ID:
        return
        
    if user.id in blocked_users:
        await update.message.reply_text("شما مسدود شده‌اید.")
        return

    text = update.message.text
    username = user.username or "NoUsername"
    first_name = user.first_name or ""
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✉️ پاسخ", callback_data=f"reply:{user.id}"),
            InlineKeyboardButton("⛔ مسدود کردن", callback_data=f"block:{user.id}")
        ]
    ])

    msg = (
        f"📩 پیام جدید\n"
        f"👤 نام: {first_name}\n"
        f"👤 یوزرنیم: @{username}\n"
        f"🆔 آیدی: {user.id}\n\n"
        f"✉️ متن:\n{text}"
    )
    
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=msg,
            reply_markup=keyboard
        )
        await update.message.reply_text("✅ پیام شما ارسال شد")
    except Exception as e:
        logger.error(f"خطا در ارسال: {e}")
        await update.message.reply_text("خطایی رخ داد")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id != ADMIN_ID:
        return

    action, user_id = query.data.split(":")
    user_id = int(user_id)

    if action == "reply":
        pending_replies[ADMIN_ID] = user_id
        await query.message.reply_text(
            "✏️ پاسخ خود را بنویسید:",
            reply_markup=ForceReply(selective=True)
        )
    elif action == "block":
        blocked_users.add(user_id)
        await query.message.reply_text(f"⛔ کاربر {user_id} مسدود شد.")

async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    if ADMIN_ID not in pending_replies:
        await update.message.reply_text("لطفاً اول روی دکمه پاسخ کلیک کنید")
        return
    
    user_id = pending_replies.pop(ADMIN_ID)
    text = update.message.text
    
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"✉️ پاسخ پیامت:\n\n{text}"
        )
        await update.message.reply_text("✅ پاسخ ارسال شد.")
    except Exception as e:
        logger.error(f"خطا در پاسخ: {e}")
        await update.message.reply_text("خطا در ارسال پاسخ")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"خطا: {context.error}")

def main():
    # ایجاد اپلیکیشن
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # افزودن هندلرها
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.REPLY & filters.TEXT, admin_reply))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, user_message))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_error_handler(error_handler)
    
    logger.info("ربات شروع به کار کرد...")
    
    # اجرای ربات
    app.run_polling()

if __name__ == "__main__":
    # شروع وب‌سرور در یک نخ جداگانه
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # اجرای ربات
    main()
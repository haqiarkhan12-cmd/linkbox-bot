import os
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)


# =========================
# CONFIG
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not configured.")


# =========================
# LOGGING
# =========================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# =========================
# MAIN MENU
# =========================

def main_menu():

    keyboard = [
        [
            InlineKeyboardButton(
                "📥 Download",
                callback_data="download"
            )
        ],
        [
            InlineKeyboardButton(
                "📁 My Files",
                callback_data="files"
            ),
            InlineKeyboardButton(
                "💎 Premium",
                callback_data="premium"
            ),
        ],
        [
            InlineKeyboardButton(
                "🌐 Language",
                callback_data="language"
            ),
            InlineKeyboardButton(
                "ℹ️ Help",
                callback_data="help"
            ),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================
# START
# =========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    text = (
        "📦 *Welcome to LinkBox* 🤖\n\n"
        "ستاسو هوښیار Link & File Assistant.\n\n"
        "🔗 خپل عامه او اجازه‌لرونکی فایل لینک "
        "راولېږئ، LinkBox به یې پروسس کړي.\n\n"
        "👇 له لاندې Menu څخه انتخاب وکړئ."
    )

    await update.message.reply_text(
        text,
        reply_markup=main_menu(),
        parse_mode="Markdown",
    )


# =========================
# BUTTON HANDLER
# =========================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    if query.data == "download":

        await query.message.reply_text(
            "📥 *Download*\n\n"
            "خپل فایل URL راولېږئ.\n\n"
            "مثال:\n"
            "`https://example.com/file.pdf`",
            parse_mode="Markdown",
        )

    elif query.data == "files":

        await query.message.reply_text(
            "📁 *My Files*\n\n"
            "ستاسو د Download تاریخچه به دلته ښکاره شي."
        )

    elif query.data == "premium":

        await query.message.reply_text(
            "💎 *LinkBox Premium*\n\n"
            "Premium features به ډېر ژر فعال شي.\n\n"
            "🚀 Faster processing\n"
            "📦 Larger files\n"
            "⭐ Higher limits"
        )

    elif query.data == "language":

        keyboard = [
            [
                InlineKeyboardButton(
                    "🇦🇫 پښتو",
                    callback_data="lang_ps"
                ),
                InlineKeyboardButton(
                    "🇬🇧 English",
                    callback_data="lang_en"
                ),
            ]
        ]

        await query.message.reply_text(
            "🌐 Select your language:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif query.data == "lang_ps":

        await query.message.reply_text(
            "🇦🇫 ژبه پښتو ته بدله شوه."
        )

    elif query.data == "lang_en":

        await query.message.reply_text(
            "🇬🇧 Language changed to English."
        )

    elif query.data == "help":

        await query.message.reply_text(
            "ℹ️ *LinkBox Help*\n\n"
            "1️⃣ Download ته لاړ شئ.\n"
            "2️⃣ خپل عامه فایل URL راولېږئ.\n"
            "3️⃣ LinkBox به لینک وګوري.\n"
            "4️⃣ که فایل مناسب وي، پروسس به یې کړي.\n\n"
            "⚠️ یوازې هغه فایلونه ترلاسه کړئ چې "
            "د ترلاسه کولو اجازه یې لرئ.",
            parse_mode="Markdown",
        )


# =========================
# URL MESSAGE
# =========================

async def handle_url(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    url = update.message.text.strip()

    if not url.startswith(("http://", "https://")):

        await update.message.reply_text(
            "❌ مهرباني وکړئ یو معتبر URL راولېږئ."
        )

        return

    await update.message.reply_text(
        "🔎 *Checking your link...*\n\n"
        "⏳ LinkBox اوس لینک بررسی کوي.",
        parse_mode="Markdown",
    )

    # Downloader system will be added next.


# =========================
# ERROR HANDLER
# =========================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):

    logger.error(
        "Exception while handling update:",
        exc_info=context.error,
    )


# =========================
# MAIN
# =========================

def main():

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CallbackQueryHandler(button_handler)
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_url
        )
    )

    application.add_error_handler(error_handler)

    print("================================")
    print("      LinkBox Bot Starting")
    print("================================")
    print("Bot is running...")

    application.run_polling()


if __name__ == "__main__":
    main()

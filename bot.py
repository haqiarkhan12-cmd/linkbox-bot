import logging
import os

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from config import BOT_TOKEN, ADMIN_ID
from database import (
    init_db,
    add_user,
    get_user,
    is_banned,
    add_download,
    update_download,
    increment_download_count,
    get_user_downloads,
    get_statistics,
    set_banned,
    set_premium,
)

from downloader import download_file, delete_file


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# ============================================================
# MAIN MENU
# ============================================================

def main_menu():

    keyboard = [
        [
            InlineKeyboardButton(
                "📥 Download",
                callback_data="download",
            )
        ],
        [
            InlineKeyboardButton(
                "📁 My Files",
                callback_data="files",
            ),
            InlineKeyboardButton(
                "💎 Premium",
                callback_data="premium",
            ),
        ],
        [
            InlineKeyboardButton(
                "🌐 Language",
                callback_data="language",
            ),
            InlineKeyboardButton(
                "ℹ️ Help",
                callback_data="help",
            ),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# ============================================================
# ADMIN MENU
# ============================================================

def admin_menu():

    keyboard = [
        [
            InlineKeyboardButton(
                "📊 Statistics",
                callback_data="admin_stats",
            ),
        ],
        [
            InlineKeyboardButton(
                "👥 Users",
                callback_data="admin_users",
            ),
        ],
        [
            InlineKeyboardButton(
                "💎 Premium",
                callback_data="admin_premium",
            ),
        ],
        [
            InlineKeyboardButton(
                "🚫 Ban User",
                callback_data="admin_ban",
            ),
            InlineKeyboardButton(
                "✅ Unban User",
                callback_data="admin_unban",
            ),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# ============================================================
# ADMIN CHECK
# ============================================================

def is_admin(user_id):

    return user_id == ADMIN_ID


# ============================================================
# START
# ============================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    await add_user(user)

    if await is_banned(user.id):

        await update.message.reply_text(
            "🚫 ستاسو اکاونټ بند شوی دی."
        )

        return

    text = (
        "📦 *Welcome to LinkBox* 🤖\n\n"
        "ستاسو هوښیار Link & File Assistant.\n\n"
        "🔗 خپل عامه او اجازه‌لرونکی فایل لینک "
        "راولېږئ.\n\n"
        "👇 له لاندې Menu څخه انتخاب وکړئ."
    )

    await update.message.reply_text(
        text,
        reply_markup=main_menu(),
        parse_mode="Markdown",
    )


# ============================================================
# ADMIN COMMAND
# ============================================================

async def admin(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    if not is_admin(user.id):

        await update.message.reply_text(
            "⛔ Access denied."
        )

        return

    await update.message.reply_text(
        "👑 *LinkBox Admin Panel*\n\n"
        "له لاندې انتخاب وکړئ:",
        reply_markup=admin_menu(),
        parse_mode="Markdown",
    )


# ============================================================
# BUTTON HANDLER
# ============================================================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    await query.answer()

    user = query.from_user

    # --------------------------------------------------------
    # BAN CHECK
    # --------------------------------------------------------

    if await is_banned(user.id):

        await query.message.reply_text(
            "🚫 ستاسو اکاونټ بند شوی دی."
        )

        return

    # --------------------------------------------------------
    # DOWNLOAD
    # --------------------------------------------------------

    if query.data == "download":

        await query.message.reply_text(
            "📥 *Download*\n\n"
            "خپل مستقیم فایل URL راولېږئ.\n\n"
            "مثال:\n"
            "`https://example.com/file.pdf`",
            parse_mode="Markdown",
        )

    # --------------------------------------------------------
    # MY FILES
    # --------------------------------------------------------

    elif query.data == "files":

        downloads = await get_user_downloads(
            user.id,
            10,
        )

        if not downloads:

            await query.message.reply_text(
                "📁 تر اوسه مو کوم فایل Download کړی نه دی."
            )

            return

        text = "📁 *Your Recent Downloads*\n\n"

        for item in downloads:

            filename = item["filename"] or "Unknown"

            status = item["status"]

            if status == "completed":
                icon = "✅"

            elif status == "failed":
                icon = "❌"

            else:
                icon = "⏳"

            text += f"{icon} `{filename}`\n"

        await query.message.reply_text(
            text,
            parse_mode="Markdown",
        )

    # --------------------------------------------------------
    # PREMIUM
    # --------------------------------------------------------

    elif query.data == "premium":

        await query.message.reply_text(
            "💎 *LinkBox Premium*\n\n"
            "🚀 Faster processing\n"
            "📦 Larger file limits\n"
            "⭐ Higher daily limits\n"
            "📁 More download history\n\n"
            "Premium payment system به وروسته اضافه کړو.",
            parse_mode="Markdown",
        )

    # --------------------------------------------------------
    # LANGUAGE
    # --------------------------------------------------------

    elif query.data == "language":

        keyboard = [
            [
                InlineKeyboardButton(
                    "🇦🇫 پښتو",
                    callback_data="lang_ps",
                ),
                InlineKeyboardButton(
                    "🇬🇧 English",
                    callback_data="lang_en",
                ),
            ]
        ]

        await query.message.reply_text(
            "🌐 Select your language:",
            reply_markup=InlineKeyboardMarkup(
                keyboard
            ),
        )

    # --------------------------------------------------------
    # PASHTO
    # --------------------------------------------------------

    elif query.data == "lang_ps":

        await query.message.reply_text(
            "🇦🇫 ژبه پښتو ته بدله شوه."
        )

    # --------------------------------------------------------
    # ENGLISH
    # --------------------------------------------------------

    elif query.data == "lang_en":

        await query.message.reply_text(
            "🇬🇧 Language changed to English."
        )

    # --------------------------------------------------------
    # HELP
    # --------------------------------------------------------

    elif query.data == "help":

        await query.message.reply_text(
            "ℹ️ *LinkBox Help*\n\n"
            "1️⃣ Download ته لاړ شئ.\n"
            "2️⃣ خپل عامه direct file URL راولېږئ.\n"
            "3️⃣ LinkBox به یې بررسی کړي.\n"
            "4️⃣ فایل به Telegram ته واستول شي.\n\n"
            "⚠️ یوازې هغه فایلونه ترلاسه کړئ چې "
            "د ترلاسه کولو اجازه یې لرئ.",
            parse_mode="Markdown",
        )

    # ========================================================
    # ADMIN
    # ========================================================

    elif query.data.startswith("admin_"):

        if not is_admin(user.id):

            await query.message.reply_text(
                "⛔ Access denied."
            )

            return

        # ----------------------------------------------------
        # STATISTICS
        # ----------------------------------------------------

        if query.data == "admin_stats":

            stats = await get_statistics()

            text = (
                "📊 *LinkBox Statistics*\n\n"
                f"👥 Users: {stats['users']}\n"
                f"📥 Downloads: {stats['downloads']}\n"
                f"✅ Completed: {stats['completed']}\n"
                f"💎 Premium: {stats['premium']}"
            )

            await query.message.reply_text(
                text,
                parse_mode="Markdown",
            )

        # ----------------------------------------------------
        # USERS
        # ----------------------------------------------------

        elif query.data == "admin_users":

            stats = await get_statistics()

            await query.message.reply_text(
                f"👥 Total registered users: "
                f"{stats['users']}"
            )

        # ----------------------------------------------------
        # PREMIUM
        # ----------------------------------------------------

        elif query.data == "admin_premium":

            await query.message.reply_text(
                "💎 Premium management\n\n"
                "د Premium management command system "
                "به بل قدم کې اضافه کړو."
            )

        # ----------------------------------------------------
        # BAN
        # ----------------------------------------------------

        elif query.data == "admin_ban":

            context.user_data["admin_action"] = "ban"

            await query.message.reply_text(
                "🚫 د هغه User Telegram ID راولېږئ "
                "چې Ban کول یې غواړئ."
            )

        # ----------------------------------------------------
        # UNBAN
        # ----------------------------------------------------

        elif query.data == "admin_unban":

            context.user_data["admin_action"] = "unban"

            await query.message.reply_text(
                "✅ د User Telegram ID راولېږئ "
                "چې Unban کول یې غواړئ."
            )


# ============================================================
# HANDLE TEXT / URL
# ============================================================

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    await add_user(user)

    # --------------------------------------------------------
    # BAN CHECK
    # --------------------------------------------------------

    if await is_banned(user.id):

        await update.message.reply_text(
            "🚫 ستاسو اکاونټ بند شوی دی."
        )

        return

    # --------------------------------------------------------
    # ADMIN ACTION
    # --------------------------------------------------------

    if (
        is_admin(user.id)
        and context.user_data.get("admin_action")
    ):

        action = context.user_data.get(
            "admin_action"
        )

        try:

            target_id = int(
                update.message.text.strip()
            )

        except ValueError:

            await update.message.reply_text(
                "❌ Telegram ID باید یوازې عدد وي."
            )

            return

        if action == "ban":

            await set_banned(
                target_id,
                True,
            )

            await update.message.reply_text(
                f"🚫 User `{target_id}` banned.",
                parse_mode="Markdown",
            )

        elif action == "unban":

            await set_banned(
                target_id,
                False,
            )

            await update.message.reply_text(
                f"✅ User `{target_id}` unbanned.",
                parse_mode="Markdown",
            )

        context.user_data.pop(
            "admin_action",
            None,
        )

        return

    # --------------------------------------------------------
    # URL
    # --------------------------------------------------------

    url = update.message.text.strip()

    if not url.startswith(
        ("http://", "https://")
    ):

        await update.message.reply_text(
            "🔗 مهرباني وکړئ یو معتبر HTTP/HTTPS "
            "فایل URL راولېږئ."
        )

        return

    # --------------------------------------------------------
    # CREATE DOWNLOAD RECORD
    # --------------------------------------------------------

    download_id = await add_download(
        user.id,
        url,
    )

    status_message = await update.message.reply_text(
        "🔎 لینک بررسی کېږي...\n\n"
        "⏳ مهرباني وکړئ انتظار وکړئ."
    )

    try:

        result = await download_file(
            url,
            user.id,
        )

        await update_download(
            download_id,
            "completed",
            result["filename"],
            result["size"],
        )

        await increment_download_count(
            user.id
        )

        size_mb = result["size"] / (
            1024 * 1024
        )

        await status_message.edit_text(
            "✅ *Download Complete*\n\n"
            f"📄 `{result['filename']}`\n"
            f"📦 {size_mb:.2f} MB\n\n"
            "📤 فایل Telegram ته لېږل کېږي...",
            parse_mode="Markdown",
        )

        # ----------------------------------------------------
        # SEND FILE
        # ----------------------------------------------------

        try:

            await update.message.reply_document(
                document=result["path"],
                caption=(
                    "📦 *LinkBox*\n"
                    "✅ Download completed."
                ),
                parse_mode="Markdown",
            )

        except Exception as send_error:

            logger.error(
                "Telegram file send error: %s",
                send_error,
            )

            await update.message.reply_text(
                "⚠️ فایل Download شو، خو Telegram "
                "ته د لېږلو پر مهال ستونزه راغله."
            )

        finally:

            delete_file(
                result["path"]
            )

        await status_message.delete()

    except Exception as error:

        logger.error(
            "Download error: %s",
            error,
        )

        await update_download(
            download_id,
            "failed",
            error_message=str(error),
        )

        await status_message.edit_text(
            "❌ *Download Failed*\n\n"
            f"Reason: `{str(error)[:500]}`",
            parse_mode="Markdown",
        )


# ============================================================
# ERROR HANDLER
# ============================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
):

    logger.error(
        "Exception while handling update:",
        exc_info=context.error,
    )


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

async def post_init(
    application: Application,
):

    await init_db()

    logger.info(
        "Database initialized successfully."
    )


# ============================================================
# MAIN
# ============================================================

def main():

    if not BOT_TOKEN:

        raise ValueError(
            "BOT_TOKEN is missing."
        )

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    application.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    application.add_handler(
        CommandHandler(
            "admin",
            admin,
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            button_handler
        )
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message,
        )
    )

    application.add_error_handler(
        error_handler
    )

    print("==============================")
    print("       LinkBox Bot")
    print("==============================")
    print("Bot is running...")

    application.run_polling()


if __name__ == "__main__":
    main()

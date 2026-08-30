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
    is_banned,
    add_download,
    update_download,
    increment_download_count,
    get_user_downloads,
    get_statistics,
    set_banned,
)

from downloader import (
    get_media_info,
    download_media,
    delete_file,
)


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# ============================================================
# MENUS
# ============================================================

def main_menu():

    keyboard = [
        [
            InlineKeyboardButton(
                "📥 Download Video",
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


def quality_menu():

    keyboard = [
        [
            InlineKeyboardButton(
                "🎬 360p",
                callback_data="quality_360",
            ),
            InlineKeyboardButton(
                "🎬 720p",
                callback_data="quality_720",
            ),
        ],
        [
            InlineKeyboardButton(
                "🎬 1080p",
                callback_data="quality_1080",
            ),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


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
# ADMIN
# ============================================================

def is_admin(user_id):

    return user_id == ADMIN_ID


async def admin(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_admin(update.effective_user.id):

        await update.message.reply_text(
            "⛔ Access denied."
        )

        return

    await update.message.reply_text(
        "👑 *LinkBox Admin Panel*",
        reply_markup=admin_menu(),
        parse_mode="Markdown",
    )


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

    await update.message.reply_text(
        "📦 *Welcome to LinkBox* 🤖\n\n"
        "🔗 د ویډیو لینک راولېږئ.\n\n"
        "LinkBox به د موجودو معلوماتو او "
        "کیفیتونو په اړه درته انتخاب درکړي.",
        reply_markup=main_menu(),
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

    if await is_banned(user.id):

        await query.message.reply_text(
            "🚫 ستاسو اکاونټ بند شوی دی."
        )

        return

    # --------------------------------------------------------
    # DOWNLOAD
    # --------------------------------------------------------

    if query.data == "download":

        context.user_data["waiting_for_url"] = True

        await query.message.reply_text(
            "🔗 *Send Video URL*\n\n"
            "د ویډیو عامه URL راولېږئ.",
            parse_mode="Markdown",
        )

    # --------------------------------------------------------
    # FILES
    # --------------------------------------------------------

    elif query.data == "files":

        downloads = await get_user_downloads(
            user.id,
            10,
        )

        if not downloads:

            await query.message.reply_text(
                "📁 تر اوسه Download موجود نه دی."
            )

            return

        text = "📁 *Recent Downloads*\n\n"

        for item in downloads:

            filename = item["filename"] or "Unknown"

            status = item["status"]

            icon = (
                "✅"
                if status == "completed"
                else "❌"
                if status == "failed"
                else "⏳"
            )

            text += (
                f"{icon} `{filename}`\n"
            )

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
            "🚀 Higher limits\n"
            "📦 Larger files\n"
            "⚡ Priority processing\n\n"
            "Payment system به وروسته اضافه کړو.",
            parse_mode="Markdown",
        )

    # --------------------------------------------------------
    # LANGUAGE
    # --------------------------------------------------------

    elif query.data == "language":

        await query.message.reply_text(
            "🌐 Language\n\n"
            "🇦🇫 پښتو\n"
            "🇬🇧 English"
        )

    # --------------------------------------------------------
    # HELP
    # --------------------------------------------------------

    elif query.data == "help":

        await query.message.reply_text(
            "ℹ️ *LinkBox Help*\n\n"
            "1️⃣ Download Video ووهئ.\n"
            "2️⃣ د ویډیو لینک راولېږئ.\n"
            "3️⃣ کیفیت انتخاب کړئ.\n"
            "4️⃣ LinkBox به فایل Telegram ته واستوي.\n\n"
            "⚠️ یوازې هغه content استعمال کړئ "
            "چې د ترلاسه کولو اجازه یې لرئ.",
            parse_mode="Markdown",
        )

    # ========================================================
    # QUALITY
    # ========================================================

    elif query.data.startswith("quality_"):

        quality = query.data.split("_")[1]

        url = context.user_data.get(
            "video_url"
        )

        if not url:

            await query.message.reply_text(
                "❌ Video URL پیدا نه شو. بیا هڅه وکړئ."
            )

            return

        await query.message.reply_text(
            f"⏳ Downloading {quality}p...\n\n"
            "مهرباني وکړئ انتظار وکړئ."
        )

        download_id = await add_download(
            user.id,
            url,
        )

        file_path = None

        try:

            result = await download_media(
                url,
                user.id,
                quality,
            )

            file_path = result["path"]

            await update_download(
                download_id,
                "completed",
                result["filename"],
                result["size"],
            )

            await increment_download_count(
                user.id
            )

            size_mb = (
                result["size"] /
                (1024 * 1024)
            )

            await query.message.reply_text(
                f"✅ Download complete!\n\n"
                f"🎬 {result['filename']}\n"
                f"📦 {size_mb:.2f} MB\n\n"
                "📤 Sending to Telegram..."
            )

            with open(
                file_path,
                "rb"
            ) as video_file:

                await query.message.reply_video(
                    video=video_file,
                    caption="📦 LinkBox",
                )

        except Exception as error:

            logger.exception(
                "Download failed"
            )

            await update_download(
                download_id,
                "failed",
                error_message=str(error),
            )

            await query.message.reply_text(
                "❌ Download failed.\n\n"
                "ممکنه ویډیو private وي، "
                "لینک unsupported وي، یا فایل "
                "د ټاکلي limit څخه لوی وي."
            )

        finally:

            if file_path:

                delete_file(
                    file_path
                )

            context.user_data.pop(
                "video_url",
                None
            )


# ============================================================
# TEXT / URL HANDLER
# ============================================================

async def handle_message(
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

    url = update.message.text.strip()

    if not url.startswith(
        ("http://", "https://")
    ):

        await update.message.reply_text(
            "🔗 مهرباني وکړئ یو معتبر video URL راولېږئ."
        )

        return

    context.user_data["video_url"] = url

    status = await update.message.reply_text(
        "🔎 *Checking video...*\n\n"
        "⏳ معلومات ترلاسه کېږي.",
        parse_mode="Markdown",
    )

    try:

        info = await get_media_info(
            url
        )

        title = info.get(
            "title",
            "Unknown"
        )

        duration = info.get(
            "duration"
        )

        uploader = info.get(
            "uploader"
        )

        duration_text = "Unknown"

        if duration:

            minutes = int(duration) // 60
            seconds = int(duration) % 60

            duration_text = (
                f"{minutes}:{seconds:02d}"
            )

        text = (
            "🎬 *Video Found*\n\n"
            f"📌 Title: `{title[:150]}`\n"
            f"👤 Creator: `{uploader or 'Unknown'}`\n"
            f"⏱ Duration: `{duration_text}`\n\n"
            "👇 Select quality:"
        )

        await status.edit_text(
            text,
            reply_markup=quality_menu(),
            parse_mode="Markdown",
        )

    except Exception as error:

        logger.exception(
            "Information extraction failed"
        )

        context.user_data.pop(
            "video_url",
            None
        )

        await status.edit_text(
            "❌ *Could not process this URL.*\n\n"
            "دا لینک ممکن private وي، "
            "unsupported وي، یا content محدود وي.",
            parse_mode="Markdown",
        )


# ============================================================
# ADMIN BUTTONS
# ============================================================

async def admin_button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not is_admin(query.from_user.id):

        await query.answer(
            "Access denied.",
            show_alert=True,
        )

        return

    await query.answer()

    if query.data == "admin_stats":

        stats = await get_statistics()

        await query.message.reply_text(
            "📊 *Statistics*\n\n"
            f"👥 Users: {stats['users']}\n"
            f"📥 Downloads: {stats['downloads']}\n"
            f"✅ Completed: {stats['completed']}\n"
            f"💎 Premium: {stats['premium']}",
            parse_mode="Markdown",
        )

    elif query.data == "admin_users":

        stats = await get_statistics()

        await query.message.reply_text(
            f"👥 Total Users: {stats['users']}"
        )

    elif query.data == "admin_ban":

        context.user_data[
            "admin_action"
        ] = "ban"

        await query.message.reply_text(
            "🚫 د User Telegram ID راولېږئ."
        )

    elif query.data == "admin_unban":

        context.user_data[
            "admin_action"
        ] = "unban"

        await query.message.reply_text(
            "✅ د User Telegram ID راولېږئ."
        )


# ============================================================
# ADMIN ID HANDLER
# ============================================================

async def handle_admin_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    if not is_admin(user.id):

        return

    action = context.user_data.get(
        "admin_action"
    )

    if not action:

        return

    try:

        target_id = int(
            update.message.text.strip()
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Telegram ID باید عدد وي."
        )

        return

    if action == "ban":

        await set_banned(
            target_id,
            True,
        )

        await update.message.reply_text(
            f"🚫 `{target_id}` banned.",
            parse_mode="Markdown",
        )

    elif action == "unban":

        await set_banned(
            target_id,
            False,
        )

        await update.message.reply_text(
            f"✅ `{target_id}` unbanned.",
            parse_mode="Markdown",
        )

    context.user_data.pop(
        "admin_action",
        None
    )


# ============================================================
# ERROR
# ============================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
):

    logger.error(
        "Unhandled exception:",
        exc_info=context.error,
    )


# ============================================================
# STARTUP
# ============================================================

async def post_init(
    application: Application,
):

    await init_db()

    logger.info(
        "Database initialized."
    )


#

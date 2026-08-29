import os
import aiosqlite
from datetime import datetime, timezone


# =========================
# DATABASE CONFIG
# =========================

DATABASE_DIR = "database"
DATABASE_FILE = os.path.join(DATABASE_DIR, "linkbox.db")


# =========================
# HELPERS
# =========================

def utc_now():
    return datetime.now(timezone.utc).isoformat()


# =========================
# INITIALIZE DATABASE
# =========================

async def init_db():

    os.makedirs(DATABASE_DIR, exist_ok=True)

    async with aiosqlite.connect(DATABASE_FILE) as db:

        # USERS
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                language TEXT DEFAULT 'ps',
                is_premium INTEGER DEFAULT 0,
                premium_until TEXT,
                is_banned INTEGER DEFAULT 0,
                downloads_count INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                last_active TEXT
            )
        """)

        # DOWNLOADS
        await db.execute("""
            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                filename TEXT,
                file_size INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                error_message TEXT,
                created_at TEXT NOT NULL,
                completed_at TEXT
            )
        """)

        # PAYMENTS
        await db.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                currency TEXT DEFAULT 'USD',
                method TEXT,
                status TEXT DEFAULT 'pending',
                transaction_id TEXT,
                created_at TEXT NOT NULL
            )
        """)

        # BOT SETTINGS
        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # ADMIN LOGS
        await db.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                action TEXT NOT NULL,
                details TEXT,
                created_at TEXT NOT NULL
            )
        """)

        await db.commit()


# =========================
# USER FUNCTIONS
# =========================

async def add_user(user):

    async with aiosqlite.connect(DATABASE_FILE) as db:

        await db.execute("""
            INSERT OR IGNORE INTO users (
                telegram_id,
                username,
                first_name,
                created_at,
                last_active
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            user.id,
            user.username,
            user.first_name,
            utc_now(),
            utc_now()
        ))

        await db.execute("""
            UPDATE users
            SET username = ?,
                first_name = ?,
                last_active = ?
            WHERE telegram_id = ?
        """, (
            user.username,
            user.first_name,
            utc_now(),
            user.id
        ))

        await db.commit()


async def get_user(telegram_id):

    async with aiosqlite.connect(DATABASE_FILE) as db:

        db.row_factory = aiosqlite.Row

        cursor = await db.execute("""
            SELECT *
            FROM users
            WHERE telegram_id = ?
        """, (telegram_id,))

        return await cursor.fetchone()


async def is_banned(telegram_id):

    user = await get_user(telegram_id)

    if not user:
        return False

    return bool(user["is_banned"])


async def set_banned(telegram_id, banned=True):

    async with aiosqlite.connect(DATABASE_FILE) as db:

        await db.execute("""
            UPDATE users
            SET is_banned = ?
            WHERE telegram_id = ?
        """, (
            1 if banned else 0,
            telegram_id
        ))

        await db.commit()


# =========================
# PREMIUM
# =========================

async def set_premium(
    telegram_id,
    premium=True,
    premium_until=None
):

    async with aiosqlite.connect(DATABASE_FILE) as db:

        await db.execute("""
            UPDATE users
            SET is_premium = ?,
                premium_until = ?
            WHERE telegram_id = ?
        """, (
            1 if premium else 0,
            premium_until,
            telegram_id
        ))

        await db.commit()


# =========================
# DOWNLOAD FUNCTIONS
# =========================

async def add_download(
    telegram_id,
    url
):

    async with aiosqlite.connect(DATABASE_FILE) as db:

        cursor = await db.execute("""
            INSERT INTO downloads (
                telegram_id,
                url,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?)
        """, (
            telegram_id,
            url,
            "pending",
            utc_now()
        ))

        download_id = cursor.lastrowid

        await db.commit()

        return download_id


async def update_download(
    download_id,
    status,
    filename=None,
    file_size=0,
    error_message=None
):

    async with aiosqlite.connect(DATABASE_FILE) as db:

        completed_at = None

        if status in ("completed", "failed"):
            completed_at = utc_now()

        await db.execute("""
            UPDATE downloads
            SET status = ?,
                filename = ?,
                file_size = ?,
                error_message = ?,
                completed_at = ?
            WHERE id = ?
        """, (
            status,
            filename,
            file_size,
            error_message,
            completed_at,
            download_id
        ))

        await db.commit()


async def increment_download_count(telegram_id):

    async with aiosqlite.connect(DATABASE_FILE) as db:

        await db.execute("""
            UPDATE users
            SET downloads_count = downloads_count + 1
            WHERE telegram_id = ?
        """, (telegram_id,))

        await db.commit()


async def get_user_downloads(
    telegram_id,
    limit=10
):

    async with aiosqlite.connect(DATABASE_FILE) as db:

        db.row_factory = aiosqlite.Row

        cursor = await db.execute("""
            SELECT *
            FROM downloads
            WHERE telegram_id = ?
            ORDER BY id DESC
            LIMIT ?
        """, (
            telegram_id,
            limit
        ))

        return await cursor.fetchall()


# =========================
# STATISTICS
# =========================

async def get_statistics():

    async with aiosqlite.connect(DATABASE_FILE) as db:

        cursor = await db.execute(
            "SELECT COUNT(*) FROM users"
        )

        total_users = (await cursor.fetchone())[0]

        cursor = await db.execute(
            "SELECT COUNT(*) FROM downloads"
        )

        total_downloads = (await cursor.fetchone())[0]

        cursor = await db.execute("""
            SELECT COUNT(*)
            FROM downloads
            WHERE status = 'completed'
        """)

        completed_downloads = (await cursor.fetchone())[0]

        cursor = await db.execute("""
            SELECT COUNT(*)
            FROM users
            WHERE is_premium = 1
        """)

        premium_users = (await cursor.fetchone())[0]

        return {
            "users": total_users,
            "downloads": total_downloads,
            "completed": completed_downloads,
            "premium": premium_users
        }


# =========================
# LOGGING
# =========================

async def add_log(
    telegram_id,
    action,
    details=""
):

    async with aiosqlite.connect(DATABASE_FILE) as db:

        await db.execute("""
            INSERT INTO logs (
                telegram_id,
                action,
                details,
                created_at
            )
            VALUES (?, ?, ?, ?)
        """, (
            telegram_id,
            action,
            details,
            utc_now()
        ))

        await db.commit()

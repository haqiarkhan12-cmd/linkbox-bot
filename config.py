import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Admin Telegram ID
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# User limits
FREE_DAILY_LIMIT = int(
    os.getenv("FREE_DAILY_LIMIT", "5")
)

PREMIUM_DAILY_LIMIT = int(
    os.getenv("PREMIUM_DAILY_LIMIT", "50")
)

# Maximum file size in MB
MAX_FILE_SIZE_MB = int(
    os.getenv("MAX_FILE_SIZE_MB", "50")
)

MAX_FILE_SIZE = (
    MAX_FILE_SIZE_MB * 1024 * 1024
)

# Download folder
DOWNLOAD_DIR = os.getenv(
    "DOWNLOAD_DIR",
    "downloads"
)

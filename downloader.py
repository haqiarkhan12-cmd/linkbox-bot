import asyncio
import os
import re
import shutil
from urllib.parse import urlparse

import yt_dlp

from config import DOWNLOAD_DIR, MAX_FILE_SIZE


# ============================================================
# DIRECTORIES
# ============================================================

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# ============================================================
# SUPPORTED URL CHECK
# ============================================================

def is_supported_url(url: str) -> bool:
    """
    Basic URL validation.
    yt-dlp determines whether the platform itself is supported.
    """

    try:
        parsed = urlparse(url)

        return (
            parsed.scheme in ("http", "https")
            and bool(parsed.netloc)
        )

    except Exception:
        return False


# ============================================================
# SAFE FILENAME
# ============================================================

def safe_filename(filename: str) -> str:

    filename = filename or "video"

    filename = re.sub(
        r'[\\/:*?"<>|]+',
        "_",
        filename
    )

    filename = filename.strip()

    if not filename:
        filename = "video"

    return filename[:150]


# ============================================================
# GET MEDIA INFORMATION
# ============================================================

async def get_media_info(url: str):

    if not is_supported_url(url):
        raise ValueError(
            "Invalid video URL."
        )

    def extract():

        options = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "noplaylist": True,
        }

        with yt_dlp.YoutubeDL(options) as ydl:

            return ydl.extract_info(
                url,
                download=False
            )

    return await asyncio.to_thread(
        extract
    )


# ============================================================
# DOWNLOAD MEDIA
# ============================================================

async def download_media(
    url: str,
    user_id: int,
    quality: str = "720"
):

    if not is_supported_url(url):

        raise ValueError(
            "Invalid video URL."
        )

    user_folder = os.path.join(
        DOWNLOAD_DIR,
        str(user_id)
    )

    os.makedirs(
        user_folder,
        exist_ok=True
    )

    output_template = os.path.join(
        user_folder,
        "%(title)s.%(ext)s"
    )

    if quality == "360":

        format_selector = (
            "bestvideo[height<=360]+bestaudio/"
            "best[height<=360]/best"
        )

    elif quality == "720":

        format_selector = (
            "bestvideo[height<=720]+bestaudio/"
            "best[height<=720]/best"
        )

    elif quality == "1080":

        format_selector = (
            "bestvideo[height<=1080]+bestaudio/"
            "best[height<=1080]/best"
        )

    else:

        format_selector = (
            "bestvideo+bestaudio/best"
        )

    options = {
        "format": format_selector,
        "outtmpl": output_template,
        "merge_output_format": "mp4",

        "noplaylist": True,

        "quiet": True,
        "no_warnings": True,

        "restrictfilenames": True,

        "max_filesize": MAX_FILE_SIZE,

        "socket_timeout": 30,

        "retries": 2,

    }

    def download():

        with yt_dlp.YoutubeDL(options) as ydl:

            info = ydl.extract_info(
                url,
                download=True
            )

            filename = ydl.prepare_filename(
                info
            )

            base, _ = os.path.splitext(
                filename
            )

            possible_files = [
                filename,
                base + ".mp4",
                base + ".mkv",
                base + ".webm",
                base + ".mov",
            ]

            final_file = None

            for path in possible_files:

                if os.path.exists(path):

                    final_file = path
                    break

            if not final_file:

                raise FileNotFoundError(
                    "Downloaded file was not found."
                )

            return {
                "path": final_file,
                "filename": os.path.basename(
                    final_file
                ),
                "size": os.path.getsize(
                    final_file
                ),
                "title": info.get(
                    "title",
                    "Video"
                ),
                "duration": info.get(
                    "duration"
                ),
                "uploader": info.get(
                    "uploader"
                ),
            }

    return await asyncio.to_thread(
        download
    )


# ============================================================
# DELETE FILE
# ============================================================

def delete_file(file_path):

    try:

        if os.path.exists(file_path):

            os.remove(file_path)

        return True

    except Exception:

        return False


# ============================================================
# DELETE USER FOLDER
# ============================================================

def delete_user_folder(user_id):

    folder = os.path.join(
        DOWNLOAD_DIR,
        str(user_id)
    )

    try:

        if os.path.exists(folder):

            shutil.rmtree(folder)

        return True

    except Exception:

        return False

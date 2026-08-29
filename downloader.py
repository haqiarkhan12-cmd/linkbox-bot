import os
import socket
import ipaddress
from urllib.parse import urlparse

import aiohttp

from config import MAX_FILE_SIZE, DOWNLOAD_DIR


# =========================
# DOWNLOAD DIRECTORY
# =========================

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# =========================
# URL SECURITY
# =========================

def validate_url(url: str):

    try:
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            return False, "Only HTTP and HTTPS links are supported."

        if not parsed.hostname:
            return False, "Invalid URL."

        hostname = parsed.hostname.lower()

        # Block localhost names
        blocked_names = {
            "localhost",
            "localhost.localdomain",
            "0.0.0.0",
            "127.0.0.1",
        }

        if hostname in blocked_names:
            return False, "This URL is not allowed."

        # Resolve hostname and block private/reserved IPs
        try:
            addresses = socket.getaddrinfo(
                hostname,
                None,
                type=socket.SOCK_STREAM
            )

            for address in addresses:

                ip = address[4][0]
                ip_obj = ipaddress.ip_address(ip)

                if (
                    ip_obj.is_private
                    or ip_obj.is_loopback
                    or ip_obj.is_link_local
                    or ip_obj.is_reserved
                    or ip_obj.is_multicast
                ):
                    return False, "Private or restricted addresses are not allowed."

        except socket.gaierror:
            return False, "Could not resolve the host."

        return True, None

    except Exception:
        return False, "Invalid URL."


# =========================
# SAFE FILENAME
# =========================

def safe_filename(filename):

    if not filename:
        filename = "downloaded_file"

    filename = os.path.basename(filename)

    allowed = (
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789"
        "._- "
    )

    filename = "".join(
        char if char in allowed else "_"
        for char in filename
    )

    filename = filename.strip()

    if not filename:
        filename = "downloaded_file"

    return filename[:150]


# =========================
# DOWNLOAD FILE
# =========================

async def download_file(url, user_id):

    valid, error = validate_url(url)

    if not valid:
        raise ValueError(error)

    user_folder = os.path.join(
        DOWNLOAD_DIR,
        str(user_id)
    )

    os.makedirs(user_folder, exist_ok=True)

    timeout = aiohttp.ClientTimeout(
        total=300,
        connect=20,
        sock_read=60
    )

    headers = {
        "User-Agent": "LinkBoxBot/1.0"
    }

    async with aiohttp.ClientSession(
        timeout=timeout,
        headers=headers
    ) as session:

        async with session.get(
            url,
            allow_redirects=True,
            max_redirects=5
        ) as response:

            if response.status != 200:
                raise ValueError(
                    f"Server returned HTTP {response.status}."
                )

            # Check Content-Length if available
            content_length = response.headers.get(
                "Content-Length"
            )

            if content_length:

                try:
                    size = int(content_length)

                    if size > MAX_FILE_SIZE:
                        raise ValueError(
                            "File is larger than the allowed limit."
                        )

                except ValueError as exc:

                    if "larger" in str(exc):
                        raise

            # Filename
            content_disposition = response.headers.get(
                "Content-Disposition",
                ""
            )

            filename = None

            if "filename=" in content_disposition:

                filename = (
                    content_disposition
                    .split("filename=", 1)[1]
                    .strip()
                    .strip('"')
                    .strip("'")
                )

            if not filename:

                path = urlparse(str(response.url)).path

                filename = os.path.basename(path)

            filename = safe_filename(filename)

            file_path = os.path.join(
                user_folder,
                filename
            )

            # Avoid overwriting files
            base, extension = os.path.splitext(
                file_path
            )

            counter = 1

            while os.path.exists(file_path):

                file_path = (
                    f"{base}_{counter}{extension}"
                )

                counter += 1

            # Download in chunks
            downloaded = 0

            with open(file_path, "wb") as file:

                async for chunk in response.content.iter_chunked(
                    64 * 1024
                ):

                    downloaded += len(chunk)

                    if downloaded > MAX_FILE_SIZE:

                        file.close()

                        try:
                            os.remove(file_path)
                        except OSError:
                            pass

                        raise ValueError(
                            "File exceeded the maximum allowed size."
                        )

                    file.write(chunk)

    return {
        "path": file_path,
        "filename": os.path.basename(file_path),
        "size": downloaded
    }


# =========================
# DELETE FILE
# =========================

def delete_file(file_path):

    try:

        if os.path.exists(file_path):
            os.remove(file_path)

        return True

    except OSError:
        return False

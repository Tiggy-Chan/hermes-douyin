"""Native Douyin tools for Hermes (registered via plugins/douyin)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from tools.registry import tool_error, tool_result

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────

COOKIE_DIR = Path.home() / ".hermes" / "douyin"
DEFAULT_COOKIE_FILE = COOKIE_DIR / "cookies.json"

COMMON_STRING = {"type": "string"}
COMMON_STRING_OPT = {"type": "string", "description": "Optional"}

# ── Availability check ────────────────────────────────────────────────


def _check_douyin_available() -> bool:
    """Check if Douyin dependencies are installed."""
    try:
        import patchright  # noqa: F401
    except ImportError:
        return False
    # Check if social-auto-upload is available
    try:
        from uploader.douyin_uploader.main import DouYinVideo  # noqa: F401
        return True
    except ImportError:
        pass
    # Try finding SAU in common locations
    import sys
    for candidate in [
        Path.home() / "social-auto-upload",
        Path.home() / "projects" / "social-auto-upload",
        Path.home() / "tools" / "social-auto-upload",
    ]:
        if (candidate / "uploader" / "douyin_uploader" / "main.py").exists():
            if str(candidate) not in sys.path:
                sys.path.insert(0, str(candidate))
            return True
    return False


# ── Helper functions ──────────────────────────────────────────────────


def _get_cookie_path(account: str = "default") -> Path:
    """Get cookie file path for an account."""
    COOKIE_DIR.mkdir(parents=True, exist_ok=True)
    return COOKIE_DIR / f"cookies_{account}.json"


def _cookie_exists(account: str = "default") -> bool:
    """Check if cookie file exists."""
    return _get_cookie_path(account).exists()


# ── Tool schemas ──────────────────────────────────────────────────────

DOUYIN_AUTH_SCHEMA = {
    "name": "douyin_auth",
    "description": (
        "Manage Douyin authentication. Actions: 'login' (QR code login to get cookies), "
        "'check' (verify if current cookie is valid), 'logout' (delete stored cookies). "
        "Login requires running in headed mode (headless=false) for QR scanning, or the QR "
        "code image will be saved to a file for manual scanning."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["login", "check", "logout"],
                "description": "Auth action to perform",
            },
            "account": {
                "type": "string",
                "description": "Account name (default: 'default'). Multiple accounts supported.",
            },
            "headless": {
                "type": "boolean",
                "description": "Run browser headless (default: true). Set false for visible browser during QR login.",
            },
        },
        "required": ["action"],
    },
}

DOUYIN_STATUS_SCHEMA = {
    "name": "douyin_status",
    "description": (
        "Get Douyin plugin status: cookie validity, account info, "
        "SAU installation status, and browser availability."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "account": {
                "type": "string",
                "description": "Account name to check (default: 'default')",
            },
        },
    },
}

DOUYIN_UPLOAD_SCHEMA = {
    "name": "douyin_upload",
    "description": (
        "Upload content to Douyin (抖音). Supports video and image note uploads. "
        "Requires valid authentication (run douyin_auth login first). "
        "Video: provide file_path. Note: provide image_paths (list). "
        "Title is max 30 characters on Douyin. "
        "Tags are auto-prefixed with #. "
        "Schedule: provide schedule_time as 'YYYY-MM-DD HH:MM' (min 2h in future)."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "content_type": {
                "type": "string",
                "enum": ["video", "note"],
                "description": "Type of content to upload",
            },
            "title": {
                "type": "string",
                "description": "Video/note title (max 30 chars)",
            },
            "file_path": {
                "type": "string",
                "description": "Path to video file (for video upload)",
            },
            "image_paths": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Paths to images (for note upload)",
            },
            "description": {
                "type": "string",
                "description": "Video description / note text",
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Hashtags (without # prefix)",
            },
            "thumbnail_path": {
                "type": "string",
                "description": "Path to custom thumbnail image (video only)",
            },
            "publish_strategy": {
                "type": "string",
                "enum": ["immediate", "scheduled"],
                "description": "Publish timing (default: immediate)",
            },
            "schedule_time": {
                "type": "string",
                "description": "Scheduled publish time 'YYYY-MM-DD HH:MM' (if strategy=scheduled)",
            },
            "account": {
                "type": "string",
                "description": "Account name (default: 'default')",
            },
            "headless": {
                "type": "boolean",
                "description": "Run browser headless (default: true)",
            },
        },
        "required": ["content_type", "title"],
    },
}


# ── Tool handlers ─────────────────────────────────────────────────────


def _handle_douyin_auth(args: Dict[str, Any]) -> str:
    """Handle douyin_auth tool calls."""
    action = args.get("action", "check")
    account = args.get("account", "default")
    headless = args.get("headless", True)
    cookie_path = str(_get_cookie_path(account))

    try:
        if action == "check":
            if not _cookie_exists(account):
                return tool_result({
                    "success": False,
                    "action": "check",
                    "message": f"No cookie file for account '{account}'. Run login first.",
                })

            if not _check_douyin_available():
                return tool_result({
                    "success": False,
                    "action": "check",
                    "message": "social-auto-upload not installed. Cannot validate cookie.",
                })

            from uploader.douyin_uploader.main import cookie_auth
            valid = cookie_auth(cookie_path)
            return tool_result({
                "success": True,
                "action": "check",
                "valid": valid,
                "account": account,
                "cookie_file": cookie_path,
                "message": "Cookie is valid" if valid else "Cookie expired or invalid",
            })

        elif action == "login":
            if not _check_douyin_available():
                return tool_error(
                    "social-auto-upload not installed.\n"
                    "Install: pip install social-auto-upload && patchright install chromium"
                )

            from uploader.douyin_uploader.main import douyin_setup

            result = douyin_setup(
                account_file=cookie_path,
                handle=True,
                return_detail=True,
                headless=headless,
            )

            if isinstance(result, dict):
                return tool_result(result)
            elif result:
                return tool_result({
                    "success": True,
                    "action": "login",
                    "account": account,
                    "cookie_file": cookie_path,
                    "message": "Login successful",
                })
            else:
                return tool_result({
                    "success": False,
                    "action": "login",
                    "message": "Login failed or timed out",
                })

        elif action == "logout":
            cookie_file = _get_cookie_path(account)
            if cookie_file.exists():
                cookie_file.unlink()
                return tool_result({
                    "success": True,
                    "action": "logout",
                    "account": account,
                    "message": "Cookie deleted. Logged out.",
                })
            return tool_result({
                "success": True,
                "action": "logout",
                "account": account,
                "message": "No cookie to delete.",
            })

        else:
            return tool_error(f"Unknown auth action: {action}")

    except Exception as e:
        logger.error(f"[Douyin] Auth error: {e}", exc_info=True)
        return tool_error(f"Douyin auth failed: {e}")


def _handle_douyin_status(args: Dict[str, Any]) -> str:
    """Handle douyin_status tool calls."""
    account = args.get("account", "default")
    cookie_path = _get_cookie_path(account)

    sau_installed = _check_douyin_available()
    cookie_exists = cookie_path.exists()
    cookie_age = None
    if cookie_exists:
        import time
        cookie_age = (time.time() - cookie_path.stat().st_mtime) / 3600

    # Check patchright/chromium
    chromium_ok = False
    try:
        import subprocess
        result = subprocess.run(
            ["patchright", "install", "--dry-run"],
            capture_output=True, timeout=10
        )
        chromium_ok = result.returncode == 0
    except Exception:
        try:
            from patchright.sync_api import sync_playwright
            chromium_ok = True
        except Exception:
            pass

    return tool_result({
        "platform": "douyin",
        "account": account,
        "sau_installed": sau_installed,
        "cookie_file": str(cookie_path),
        "cookie_exists": cookie_exists,
        "cookie_age_hours": round(cookie_age, 1) if cookie_age else None,
        "chromium_available": chromium_ok,
        "ready": sau_installed and cookie_exists and (cookie_age is not None and cookie_age < 168),
    })


def _handle_douyin_upload(args: Dict[str, Any]) -> str:
    """Handle douyin_upload tool calls."""
    content_type = args.get("content_type", "video")
    title = args.get("title", "")
    account = args.get("account", "default")
    headless = args.get("headless", True)
    cookie_path = str(_get_cookie_path(account))

    if not title:
        return tool_error("Title is required")

    if not _check_douyin_available():
        return tool_error(
            "social-auto-upload not installed.\n"
            "Install: pip install social-auto-upload && patchright install chromium"
        )

    if not _cookie_exists(account):
        return tool_error(
            f"No cookie for account '{account}'. Run douyin_auth login first."
        )

    try:
        if content_type == "video":
            file_path = args.get("file_path", "")
            if not file_path:
                return tool_error("file_path is required for video upload")
            if not Path(file_path).exists():
                return tool_error(f"Video file not found: {file_path}")

            from uploader.douyin_uploader.main import DouYinVideo

            publish_date = 0
            publish_strategy = args.get("publish_strategy", "immediate")
            schedule_time = args.get("schedule_time", "")
            if publish_strategy == "scheduled" and schedule_time:
                from datetime import datetime
                publish_date = datetime.strptime(schedule_time, "%Y-%m-%d %H:%M")

            uploader = DouYinVideo(
                title=title[:30],
                file_path=file_path,
                tags=args.get("tags", []),
                publish_date=publish_date,
                account_file=cookie_path,
                thumbnail_landscape_path=args.get("thumbnail_path", ""),
                productLink="",
                productTitle="",
                thumbnail_portrait_path="",
                desc=args.get("description", ""),
                publish_strategy=publish_strategy,
                debug=False,
                headless=headless,
            )

            result = uploader.main()

            if result:
                return tool_result({
                    "success": True,
                    "content_type": "video",
                    "title": title,
                    "message": "Video uploaded successfully to Douyin",
                })
            else:
                return tool_result({
                    "success": False,
                    "content_type": "video",
                    "message": "Upload returned false. Check browser logs or try headless=false for debugging.",
                })

        elif content_type == "note":
            image_paths = args.get("image_paths", [])
            if not image_paths:
                return tool_error("image_paths is required for note upload")

            for img in image_paths:
                if not Path(img).exists():
                    return tool_error(f"Image not found: {img}")

            from uploader.douyin_uploader.main import DouYinNote

            publish_date = 0
            publish_strategy = args.get("publish_strategy", "immediate")
            schedule_time = args.get("schedule_time", "")
            if publish_strategy == "scheduled" and schedule_time:
                from datetime import datetime
                publish_date = datetime.strptime(schedule_time, "%Y-%m-%d %H:%M")

            uploader = DouYinNote(
                image_paths=image_paths,
                note=args.get("description", ""),
                tags=args.get("tags", []),
                publish_date=publish_date,
                account_file=cookie_path,
                title=title[:30],
                publish_strategy=publish_strategy,
                debug=False,
                headless=headless,
            )

            result = uploader.douyin_upload_note()

            if result:
                return tool_result({
                    "success": True,
                    "content_type": "note",
                    "title": title,
                    "message": "Image note uploaded successfully to Douyin",
                })
            else:
                return tool_result({
                    "success": False,
                    "content_type": "note",
                    "message": "Upload returned false. Check browser logs.",
                })

        else:
            return tool_error(f"Unknown content_type: {content_type}")

    except Exception as e:
        logger.error(f"[Douyin] Upload error: {e}", exc_info=True)
        return tool_error(f"Douyin upload failed: {e}")

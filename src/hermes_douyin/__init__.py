"""Douyin (抖音) integration plugin — registers 3 tools.

Tools:
  - douyin_auth:    Login (QR), check cookie, logout
  - douyin_status:  Plugin & account status
  - douyin_upload:  Upload video or image note to Douyin

Uses social-auto-upload as the backend for browser automation.
Cookie files stored at ~/.hermes/douyin/cookies_<account>.json.
"""

from __future__ import annotations

from hermes_douyin.tools import (
    DOUYIN_AUTH_SCHEMA,
    DOUYIN_STATUS_SCHEMA,
    DOUYIN_UPLOAD_SCHEMA,
    _check_douyin_available,
    _handle_douyin_auth,
    _handle_douyin_status,
    _handle_douyin_upload,
)

_TOOLS = (
    ("douyin_auth",    DOUYIN_AUTH_SCHEMA,    _handle_douyin_auth,    "🔐"),
    ("douyin_status",  DOUYIN_STATUS_SCHEMA,  _handle_douyin_status,  "📊"),
    ("douyin_upload",  DOUYIN_UPLOAD_SCHEMA,  _handle_douyin_upload,  "🎵"),
)


def register(ctx) -> None:
    """Register all Douyin tools. Called once by the plugin loader."""
    for name, schema, handler, emoji in _TOOLS:
        ctx.register_tool(
            name=name,
            toolset="douyin",
            schema=schema,
            handler=handler,
            check_fn=_check_douyin_available,
            emoji=emoji,
        )

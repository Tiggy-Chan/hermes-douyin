# hermes-douyin

Douyin (抖音) integration plugin for [Hermes Agent](https://hermes-agent.nousresearch.com).

Upload videos and image notes to Douyin via browser automation, powered by [social-auto-upload](https://github.com/dreammis/social-auto-upload).

## Features

- 🎬 **Video Upload** — Upload videos with title, description, tags, thumbnail
- 📸 **Image Note Upload** — Upload image carousels with text
- 🔐 **QR Code Login** — Authenticate via Douyin mobile app QR scan
- ⏰ **Scheduled Publishing** — Schedule posts for future dates
- 🔒 **Multi-Account** — Support multiple Douyin accounts

## Tools

| Tool | Description |
|------|-------------|
| `douyin_auth` | Login (QR), check cookie validity, logout |
| `douyin_status` | Plugin status, cookie info, dependency check |
| `douyin_upload` | Upload video or image note to Douyin |

## Installation

### 1. Install dependencies

```bash
pip install social-auto-upload
patchright install chromium
```

### 2. Symlink to Hermes plugins

```bash
ln -sf ~/projects/hermes-douyin ~/.hermes/plugins/douyin
```

### 3. Enable in config.yaml (optional)

```yaml
plugins:
  enabled:
    - douyin
```

### 4. Restart Hermes gateway

```bash
hermes gateway restart
```

## Usage

### Login

```
/douyin auth login
```

This opens a browser window with a QR code. Scan it with the Douyin mobile app.

### Check Status

```
/douyin status
```

### Upload Video

The agent will use the `douyin_upload` tool:

```json
{
  "content_type": "video",
  "title": "My Video Title",
  "file_path": "/path/to/video.mp4",
  "description": "Video description",
  "tags": ["tag1", "tag2"]
}
```

### Upload Image Note

```json
{
  "content_type": "note",
  "title": "My Note Title",
  "image_paths": ["/path/to/img1.jpg", "/path/to/img2.jpg"],
  "description": "Note text",
  "tags": ["tag1"]
}
```

### Scheduled Upload

```json
{
  "content_type": "video",
  "title": "Scheduled Video",
  "file_path": "/path/to/video.mp4",
  "publish_strategy": "scheduled",
  "schedule_time": "2026-05-15 18:00"
}
```

## Architecture

```
hermes-douyin/
├── plugin.yaml              # Plugin manifest (kind: backend)
├── __init__.py              # Entry point: register(ctx) → ctx.register_tool()
├── pyproject.toml           # Package config
└── src/hermes_douyin/
    ├── __init__.py           # Tool registration
    └── tools.py              # Tool schemas + handlers
```

Uses `social-auto-upload` as the backend for browser automation.
Cookie files stored at `~/.hermes/douyin/cookies_<account>.json`.

## Cookie Management

- Cookies are Playwright `storage_state` JSON files
- Valid for ~7 days before re-login needed
- After each upload, cookies are auto-refreshed
- Multiple accounts supported via `account` parameter

## Troubleshooting

### "social-auto-upload not installed"

```bash
pip install social-auto-upload
```

### "Chromium not found"

```bash
patchright install chromium
```

### Upload fails silently

Try `headless: false` to see the browser:

```json
{
  "content_type": "video",
  "title": "Test",
  "file_path": "/path/to/video.mp4",
  "headless": false
}
```

### Cookie expired

```bash
# Re-login
douyin_auth login account=default
```

## License

MIT

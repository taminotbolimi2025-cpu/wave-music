import os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8738282936:AAHPZONZS9BVFH1F8vVQpQCo6HBXOUkStfg")
BOT_USERNAME = "music_abdu_bot"
HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 8080))
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

# Render.com automatically sets RENDER_EXTERNAL_URL to the public HTTPS domain
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")
if RENDER_URL and not RENDER_URL.startswith("http"):
    RENDER_URL = f"https://{RENDER_URL}".rstrip("/")
elif RENDER_URL:
    RENDER_URL = RENDER_URL.rstrip("/")

WEBAPP_URL = os.environ.get("WEBAPP_URL", RENDER_URL or f"http://localhost:{PORT}")
if WEBAPP_URL and not WEBAPP_URL.startswith("http"):
    WEBAPP_URL = f"https://{WEBAPP_URL}".rstrip("/")
elif WEBAPP_URL:
    WEBAPP_URL = WEBAPP_URL.rstrip("/")

# Primary Admin ID (Owner)
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8957090868"))

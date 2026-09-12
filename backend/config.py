import os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8738282936:AAHPZONZS9BVFH1F8vVQpQCo6HBXOUkStfg")
BOT_USERNAME = "music_abdu_bot"
HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 8080))
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

# Render.com automatically sets RENDER_EXTERNAL_URL to the public HTTPS domain
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")
WEBAPP_URL = os.environ.get("WEBAPP_URL", RENDER_URL or f"http://localhost:{PORT}")
# Primary Admin ID (Owner)
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8957090868"))

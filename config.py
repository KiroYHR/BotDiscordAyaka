import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "").strip()
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-3.6-flash")

DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "").strip()
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "").strip()
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI", "https://ayaka-bot-0ywq.onrender.com/callback")

if not DISCORD_BOT_TOKEN:
    raise ValueError("Lỗi: DISCORD_BOT_TOKEN chưa được cấu hình trong file .env")

if not GEMINI_API_KEY:
    raise ValueError("Lỗi: GEMINI_API_KEY chưa được cấu hình trong file .env")

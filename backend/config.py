import os
from dotenv import load_dotenv

load_dotenv()

# Environment
ENV = os.getenv("ENV", "development")  # development | production
DEBUG = os.getenv("DEBUG", "true").lower() == "true" if ENV == "development" else False

# K2 API - using api.k2think.ai production endpoint
K2_THINK_BASE_URL = os.getenv("K2_THINK_BASE_URL", "https://api.k2think.ai/v1")
K2_INSTRUCT_BASE_URL = os.getenv("K2_INSTRUCT_BASE_URL", "https://api.k2think.ai/v1")
K2_API_KEY = os.getenv("K2_API_KEY", "")
K2_THINK_MODEL = os.getenv("K2_THINK_MODEL", "MBZUAI-IFM/K2-Think-v2")
K2_INSTRUCT_MODEL = os.getenv("K2_INSTRUCT_MODEL", "MBZUAI-IFM/K2-Think-v2")

# OpenAI API - fallback if K2 is unavailable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # Cost-effective default

# OpenClaw
USE_OPENCLAW = os.getenv("USE_OPENCLAW", "false").lower() == "true"
OPENCLAW_BASE_URL = os.getenv("OPENCLAW_BASE_URL", "http://localhost:18789")
OPENCLAW_TOKEN = os.getenv("OPENCLAW_TOKEN", "")
OPENCLAW_AGENT_ID = "department-ai"

# Database (support both relative and absolute paths)
DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "..", "data", "teamai.db"))
CHROMA_PATH = os.getenv("CHROMA_PATH", os.path.join(os.path.dirname(__file__), "..", "data", "chroma"))

# Notion
NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "")

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# SMTP Email (for task dispatch)
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")

# Email Forwarding (IMAP for receiving emails)
TEAMAI_EMAIL = os.getenv("TEAMAI_EMAIL", "")
TEAMAI_EMAIL_PASSWORD = os.getenv("TEAMAI_EMAIL_PASSWORD", "")
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
EMAIL_POLLING_INTERVAL = int(os.getenv("EMAIL_POLLING_INTERVAL", "30"))

# Security (for production)
API_KEY = os.getenv("API_KEY", "")  # Optional API key for authentication
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")  # Comma-separated list

# App
APP_TITLE = "TeamAI - Department Intelligence System"
PORT = int(os.getenv("PORT", "8001"))
SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8001")  # Public URL for download links

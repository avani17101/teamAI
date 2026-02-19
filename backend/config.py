import os
from dotenv import load_dotenv

load_dotenv()

# K2 API
K2_THINK_BASE_URL = "http://build-api-2.ifmapp.net:8000"
K2_INSTRUCT_BASE_URL = "http://instruct-api-3.ifmapp.net:8000"
K2_API_KEY = os.getenv("K2_API_KEY", "sk-XRQV0fFqJ7VfUIcfswIpZTckzFfL8LTqC1M2R1O30z7d2KQA2S")
K2_THINK_MODEL = "LLM360/K2-Think-V2"
K2_INSTRUCT_MODEL = "LLM360/K2-V2-Instruct"

# OpenClaw
OPENCLAW_BASE_URL = os.getenv("OPENCLAW_BASE_URL", "http://localhost:18789")
OPENCLAW_TOKEN = os.getenv("OPENCLAW_TOKEN", "")
OPENCLAW_AGENT_ID = "department-ai"

# Database
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "teamai.db")
CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "chroma")

# Notion
NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "30a4529e-75ee-80b0-8e33-e1d6c582a95c")

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# SMTP Email (for task dispatch)
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = os.getenv("SMTP_PORT", "587")
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")

# Email Forwarding (IMAP for receiving emails)
TEAMAI_EMAIL = os.getenv("TEAMAI_EMAIL", "")  # teamai@gmail.com
TEAMAI_EMAIL_PASSWORD = os.getenv("TEAMAI_EMAIL_PASSWORD", "")  # App password
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
EMAIL_POLLING_INTERVAL = int(os.getenv("EMAIL_POLLING_INTERVAL", "30"))  # seconds

# App
APP_TITLE = "TeamAI - Department Intelligence System"

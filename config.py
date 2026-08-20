import os
from dotenv import load_dotenv

load_dotenv()

# ==========================
# Telegram Bot
# ==========================

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError(
        "TELEGRAM_BOT_TOKEN غير موجود. "
        "ضع التوكن في متغيرات البيئة."
    )

# ==========================
# Database
# ==========================

DB_NAME = os.getenv("DB_NAME", "numbers.db")

# ==========================
# Bot Information
# ==========================

BOT_NAME = "Number Directory"
BOT_VERSION = "1.0.0"
# config.py
from dotenv import load_dotenv
import os

# .env faylni yuklaymiz
load_dotenv()

# Asosiy o'zgaruvchilar
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Iltimos .env faylida BOT_TOKEN ni o'rnating")

# ADMIN_LIST - vergul bilan ajratilgan telegram user idlar (yoki ADMIN_ID bitta bo'lsa ham ishlaydi)
_admins = os.getenv("ADMIN_LIST") or os.getenv("ADMIN_ID") or ""
if _admins.strip() == "":
    ADMIN_LIST = []
else:
    try:
        ADMIN_LIST = [int(x.strip()) for x in _admins.split(",") if x.strip()]
    except ValueError:
        raise RuntimeError("ADMIN_LIST ichidagi qiymatlar butun son (telegram id) bo'lishi kerak. Misol: 12345,67890")

# KANAL ID (raqamli -100... yoki username '@kanalnomi')
# .env da typo bo'lsa (masalan CHENNEL_ID) - uni ham qamrab olamiz
_channel = os.getenv("CHANNEL_ID") or os.getenv("CHENNEL_ID")
if _channel:
    try:
        CHANNEL_ID = int(_channel)
    except ValueError:
        CHANNEL_ID = _channel  # masalan '@kanalnomi'
else:
    CHANNEL_ID = None

# Kanalga ochiq URL/link (masalan https://t.me/kanal)
CHANNEL_LINK = os.getenv("CHANNEL_LINK") or None

# Guruh yoki boshqa idlar (ixtiyoriy)
GROUP_ID = os.getenv("GROUP_ID")
if GROUP_ID:
    try:
        GROUP_ID = int(GROUP_ID)
    except ValueError:
        pass

# Agar boshqa sozlamalar kerak bo'lsa shu yerga qo'shing
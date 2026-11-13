# Developed by ADx
from os import environ 

def _int_env(name, default):
    try:
        return int(environ.get(name, default))
    except (TypeError, ValueError):
        return int(default)

class Config:
    
    API_ID = environ.get("API_ID", "00")
    API_HASH = environ.get("API_HASH", "")
    BOT_TOKEN = environ.get("BOT_TOKEN", "") 
    BOT_OWNER_ID = [int(id) for id in environ.get("BOT_OWNER_ID", "").split() if id.strip().isdigit()]
    BOT_SESSION = environ.get("BOT_SESSION", "bot") 

    PICS = (environ.get('PICS', 'https://files.catbox.moe/uevfz8.jpg'))
    
    DATABASE_URI = environ.get("DATABASE_URI", "")
    DATABASE_NAME = environ.get("DATABASE_NAME", "Cluster0")
    
    LOG_CHANNEL = _int_env("LOG_CHANNEL", "0")
    FORCE_SUB_CHANNEL = environ.get("FORCE_SUB_CHANNEL", "") # FORCE SUB channel link 
    FORCE_SUB_ON = environ.get("FORCE_SUB_ON", "True")  # FORCE SUB ON - OFF

    # ---------------------------------------------------------------- #
    # Branding - change these to re-brand the bot without touching code
    # ---------------------------------------------------------------- #
    BOT_NAME = environ.get("BOT_NAME", "ADx Auto Forward Bot")
    BOT_USERNAME = environ.get("BOT_USERNAME", "ADxAutoForwardBot")
    DEVELOPER_NAME = environ.get("DEVELOPER_NAME", "ADx")
    UPDATES_CHANNEL = environ.get("UPDATES_CHANNEL", "https://t.me/ADxUpdates")
    SUPPORT_GROUP = environ.get("SUPPORT_GROUP", "https://t.me/ADxSupport")
    REPO_URL = environ.get("REPO_URL", "https://github.com/adgamerx/ADx-AutoForward-Bot")
    VERSION = environ.get("BOT_VERSION", "V-3.0.0")

    # Auto forward watcher
    AUTOFORWARD_INTERVAL = _int_env("AUTOFORWARD_INTERVAL", "30")  # seconds between checks
    AUTOFORWARD_BATCH = _int_env("AUTOFORWARD_BATCH", "100")  # messages per Telegram call
    AUTOFORWARD_MAX_PER_CYCLE = _int_env("AUTOFORWARD_MAX_PER_CYCLE", "300")  # backlog drained per check


class temp(object): 
    lock = {}
    CANCEL = {}
    forwardings = 0
    BANNED_USERS = []
    IS_FRWD_CHAT = []
    FORWARD_TASKS = {}
    

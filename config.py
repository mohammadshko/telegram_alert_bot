import os

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
CHANNEL_ID: str = os.getenv("CHANNEL_ID", "")
CHECK_INTERVAL: int = int(os.getenv("CHECK_INTERVAL", "60"))
DATA_DIR: str = os.getenv("DATA_DIR", "data")

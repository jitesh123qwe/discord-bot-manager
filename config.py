import os
from dotenv import load_dotenv

load_dotenv()  # <- .env file ko padhta hai

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_ID = int(os.getenv("ADMIN_ID", "YOUR_DISCORD_USER_ID_HERE"))
API_SECRET = os.getenv("API_SECRET", "your-super-secret-key-here")
DATABASE = "bot_data.db"
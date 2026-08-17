import threading
from bot import bot
from api import app, set_bot_instance
from config import BOT_TOKEN

def run_api():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

if __name__ == "__main__":
    set_bot_instance(bot)
    threading.Thread(target=run_api, daemon=True).start()
    bot.run(BOT_TOKEN)
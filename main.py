import os
import sys

import dotenv

from bot.client import Bot

if __name__ == "__main__":
    dotenv.load_dotenv()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        sys.exit("DISCORD_TOKEN environment variable is not set")
    Bot().run(token)

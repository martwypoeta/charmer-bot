from bot.client import Bot
from bot.lib import add_cogs


async def setup(bot: Bot):
    cogs = ("bot.cogs.info.help", "bot.cogs.info.user")

    await add_cogs(bot, cogs)

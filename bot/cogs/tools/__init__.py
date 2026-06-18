from bot.client import Bot
from bot.lib import add_cogs


async def setup(bot: Bot):
    cogs = (
        "bot.cogs.tools.screenshot",
        "bot.cogs.tools.password",
        "bot.cogs.tools.remind",
        "bot.cogs.tools.ip",
        "bot.cogs.tools.subdomains",
    )

    await add_cogs(bot, cogs)

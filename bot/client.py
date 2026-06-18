import asyncio
import datetime
import os
import traceback
from typing import Optional

from aiofiles import os as aio_os
from aiofiles.os import listdir
from asyncpg import Pool
from discord import AllowedMentions, Intents, Activity, ActivityType
from discord.ext import commands

from bot.lib import create_pool


class Bot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(
            intents=Intents.all(),
            command_prefix=commands.when_mentioned_or(";"),
            case_insensitive=True,
            strip_after_prefix=True,
            help_command=None,
            allowed_mentions=AllowedMentions(
                everyone=False,
                users=False,
                roles=False,
                replied_user=False,
            ),
            activity=Activity(type=ActivityType.listening, name="Spotify")
        )
        self.boot: datetime.datetime = datetime.datetime.now(datetime.UTC)
        self.pool: Optional[Pool] = None
        self.command_groups: dict[str, list[commands.Command]] = {}
        self.run()

    def run(self) -> None:
        super().run(token=os.getenv("DISCORD_TOKEN"), reconnect=True)

    async def setup_hook(self) -> None:
        self.pool = await create_pool()

        all_categories = await aio_os.listdir("bot/cogs")
        categories = [
            category
            for category in all_categories
            if await aio_os.path.isdir(f"bot/cogs/{category}")
        ]

        tasks = [self.load_extension(f"bot.cogs.{category}") for category in categories]

        try:
            await asyncio.gather(*tasks)
        except commands.ExtensionAlreadyLoaded:
            pass
        except Exception as e:
            traceback.print_exception(type(e), e, e.__traceback__)

        categorize_tasks = [
            self.categorize_commands(category) for category in categories
        ]
        await asyncio.gather(*categorize_tasks)

    async def on_close(self) -> None:
        if self.pool:
            await self.pool.close()

    async def categorize_commands(self, category: str) -> None:
        if category == "owners":
            return

        category_files = await listdir(f"bot/cogs/{category}")
        category_commands = []

        for file in category_files:
            if file.endswith(".py") and not file.startswith("_"):
                cog_name = file[:-3].capitalize()
                cog = self.get_cog(cog_name)

                if cog:
                    commands = cog.get_commands()
                    for command in commands:
                        if not command.hidden:
                            category_commands.append(
                                {
                                    "name": command.name,
                                    "aliases": getattr(command, "aliases", []),
                                    "description": getattr(command, "description", ""),
                                    "usage": getattr(command, "usage", ""),
                                }
                            )

        self.command_groups[category] = category_commands

    async def on_command_error(
            self, ctx: commands.Context, exception: commands.CommandError
    ) -> None:
        ignored_errors = (
            commands.CommandNotFound,
            commands.CheckFailure,
        )

        if isinstance(exception, ignored_errors):
            return

        raw_errors = (
            commands.BadArgument,
            commands.TooManyArguments,
            commands.BadUnionArgument,
            commands.CommandOnCooldown,
            commands.ArgumentParsingError,
            commands.UserInputError,
        )

        if isinstance(exception, raw_errors):
            return await ctx.reply(str(exception).capitalize())

        if isinstance(exception, commands.CommandInvokeError):
            traceback.print_exception(
                type(exception.original),
                exception.original,
                exception.original.__traceback__,
            )
            await ctx.reply(
                "An unexpected error occurred. Check console for more details."
            )

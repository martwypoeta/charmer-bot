import os
import re
import ssl
import time
import urllib.parse
import urllib.request
from io import BytesIO
from typing import Any, cast

from discord import (
    ButtonStyle,
    Embed,
    File,
    Interaction,
    MediaGalleryItem,
    Member,
    Message,
    User,
)
from discord.ext import commands
from discord.ui import (
    ActionRow,
    Button,
    Container,
    LayoutView,
    MediaGallery,
    Section,
    Separator,
    Thumbnail,
)
from psycopg.rows import dict_row


class ScreenshotLayout(LayoutView):
    def __init__(
        self,
        url: str,
        author: User | Member,
        command_message: Message,
        *,
        elapsed: float,
        size_kb: float,
        timeout: float = 30,
    ) -> None:
        super().__init__(timeout=timeout)
        self._author_id = author.id
        self._command_message = command_message
        self.message: Message | None = None

        header = f"## [Screenshot]({url})\n-# Requested by {author.display_name}"
        stats = f"**Time** — {elapsed:.2f} seconds\n**Size** — {size_kb:.2f} kb"

        self._delete_btn = Button(label="Delete Message", style=ButtonStyle.danger)
        self._delete_btn.callback = cast(Any, self._on_delete)

        container = Container(
            Section(
                f"{header}\n\n{stats}",
                accessory=Thumbnail(
                    author.display_avatar.url,
                    description=author.display_name,
                ),
            ),
            Separator(visible=True),
            MediaGallery(
                MediaGalleryItem(
                    "attachment://screenshot.png",
                    description=url,
                ),
            ),
            ActionRow(
                Button(label="Visit Site", url=url, style=ButtonStyle.link),
                self._delete_btn,
            ),
        )
        self.add_item(container)

    async def _on_delete(self, interaction: Interaction) -> None:
        if interaction.user.id != self._author_id:
            return await interaction.response.defer()
        await interaction.response.defer()
        if interaction.message is not None:
            await interaction.message.delete()
        await self._command_message.add_reaction("😼")

    async def on_timeout(self) -> None:
        self._delete_btn.disabled = True
        if self.message:
            await self.message.edit(view=self)


class Screenshot(commands.Cog):
    _ADMIN_REQUIRED = "You need the Administrator permission to use this command."

    def __init__(self, bot):
        self.bot = bot
        self.api_token = os.getenv("SCREENSHOT_API_TOKEN")

    @staticmethod
    def _is_administrator(ctx: commands.Context) -> bool:
        return (
            ctx.guild is not None
            and isinstance(ctx.author, Member)
            and ctx.author.guild_permissions.administrator
        )

    @commands.group(aliases=["ss", "webshot"], invoke_without_command=True)
    async def screenshot(self, ctx: commands.Context, *, url: str) -> None:
        async with self.bot.db.connection() as connection:
            cur = await connection.execute(
                "SELECT 1 FROM ss_grants WHERE user_id = %s",
                (ctx.author.id,),
            )
            if not self._is_administrator(ctx) and not await cur.fetchone():
                await ctx.reply(
                    "You are not permitted to use this command. "
                    "Ask an admin to grant you permissions."
                )
                return

        start = time.time()

        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        URL_REGEX = re.compile(
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
        )

        if not URL_REGEX.fullmatch(url):
            await ctx.reply("Incorrect URL format.")

        await ctx.typing()

        try:
            screenshot_data = await self.capture_screenshot(url)
            elapsed = time.time() - start

            if screenshot_data:
                file = File(screenshot_data, filename="screenshot.png")
                size_kb = screenshot_data.getbuffer().nbytes / 1024

                view = ScreenshotLayout(
                    url,
                    ctx.author,
                    ctx.message,
                    elapsed=elapsed,
                    size_kb=size_kb,
                )
                view.message = await ctx.reply(file=file, view=view)
            else:
                await ctx.reply("Failed to capture screenshot. Please try again later.")

        except Exception as e:
            await ctx.reply(f"An error occurred: {e}")

    async def capture_screenshot(self, url: str) -> BytesIO:
        encoded_url = urllib.parse.quote_plus(url)
        query = "https://shot.screenshotapi.net/screenshot"
        query += f"?token={self.api_token}&url={encoded_url}&output=image&file_type=png"

        with urllib.request.urlopen(
            query, context=ssl._create_unverified_context()
        ) as response:
            screenshot_data = BytesIO(response.read())
            screenshot_data.seek(0)
            return screenshot_data

    @screenshot.command(name="list", aliases=["ls"])
    async def _list(self, ctx: commands.Context) -> None:
        if not self._is_administrator(ctx):
            await ctx.reply(self._ADMIN_REQUIRED)
            return

        async with (
            self.bot.db.connection() as connection,
            connection.cursor(row_factory=dict_row) as cur,
        ):
            await cur.execute("SELECT * FROM ss_grants")
            grants = await cur.fetchall()

            if not grants:
                await ctx.reply("No permissions granted.")
                return

            embed = (
                Embed(
                    title="Users with screenshot permissions",
                    description=(
                        (
                            f"{
                                ', '.join(
                                    f'<@{user["user_id"]}>' for user in grants[:20]
                                )
                            } "
                            f"*(and {len(grants) - 20} more)*"
                        )
                        if len(grants) > 20
                        else ", ".join(f"<@{user['user_id']}>" for user in grants)
                    ),
                )
                .set_author(
                    name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url
                )
                .set_footer(text=f"{len(grants)} user(s) with screenshot permissions.")
            )

            await ctx.reply(embed=embed)

    @screenshot.command(name="grant")
    async def grant(self, ctx: commands.Context, user: User) -> None:
        if not self._is_administrator(ctx):
            await ctx.reply(self._ADMIN_REQUIRED)
            return

        async with self.bot.db.connection() as connection:
            cur = await connection.execute(
                "SELECT 1 FROM ss_grants WHERE user_id = %s",
                (user.id,),
            )
            if await cur.fetchone():
                await ctx.reply(f"{user.mention} already has permissions.")
                return

            await connection.execute(
                "INSERT INTO ss_grants VALUES (%s, %s)",
                (user.id, ctx.author.id),
            )

            await ctx.reply(f"Granted {user.mention} permissions.")

    @screenshot.command(name="revoke")
    async def revoke(self, ctx: commands.Context, user: User) -> None:
        if not self._is_administrator(ctx):
            await ctx.reply(self._ADMIN_REQUIRED)
            return

        async with self.bot.db.connection() as connection:
            cur = await connection.execute(
                "SELECT 1 FROM ss_grants WHERE user_id = %s",
                (user.id,),
            )
            if not await cur.fetchone():
                await ctx.reply(f"{user.mention} does not have permissions.")
                return

            await connection.execute(
                "DELETE FROM ss_grants WHERE user_id = %s",
                (user.id,),
            )

            await ctx.reply(f"Revoked {user.mention} permissions.")

import re
import time
import urllib.parse
import urllib.request
import ssl
import os
from io import BytesIO

from discord import ButtonStyle, Embed, File, Interaction, User
from discord.ext import commands
from discord.ui import Button, View, button

from bot.client import Bot


class Screenshot(commands.Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.api_token = os.getenv("SCREENSHOT_API_TOKEN")
        ssl._create_default_https_context = ssl._create_unverified_context

    @staticmethod
    def _is_administrator(ctx: commands.Context) -> bool:
        return (
            ctx.guild is not None
            and ctx.author.guild_permissions.administrator
        )

    @commands.group(aliases=["ss", "webshot"], invoke_without_command=True)
    async def screenshot(self, ctx: commands.Context, *, url: str) -> None:
        async with self.bot.pool.acquire() as connection:
            grants = await connection.fetch(
                "SELECT * FROM ss_grants WHERE user_id = $1",
                ctx.author.id,
            )

            if not self._is_administrator(ctx) and not grants:
                await ctx.reply(
                    "You are not permitted to use this command. Ask an admin to grant you permissions."
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

                embed = (
                    Embed(description=f"Screenshot of {url}", color=0x2A2D30)
                    .add_field(name="Time taken", value=f"{elapsed:.2f} seconds")
                    .add_field(
                        name="Bytes",
                        value=f"{screenshot_data.getbuffer().nbytes / 1024:.2f} kb",
                    )
                    .set_image(url="attachment://screenshot.png")
                    .set_author(
                        name=ctx.author.display_name,
                        icon_url=ctx.author.display_avatar.url,
                    )
                )

                class Delete(View):
                    def __init__(self, *, author: User, timeout: int = 180) -> None:
                        super().__init__(timeout=timeout)
                        self.author = author

                        self.add_item(Button(label="visit site", url=url))

                    def check(self, interaction: Interaction) -> bool:
                        return interaction.user.id == self.author.id

                    @button(label="delete message", style=ButtonStyle.red)
                    async def delete(
                            self, interaction: Interaction, button: Button
                    ) -> None:
                        if not self.check(interaction):
                            return await interaction.response.defer()

                        await interaction.message.delete()

                await ctx.reply(file=file, embed=embed, view=Delete(author=ctx.author))
            else:
                await ctx.reply("Failed to capture screenshot. Please try again later.")

        except Exception as e:
            await ctx.reply(f"An error occurred: {e}")

    async def capture_screenshot(self, url: str) -> BytesIO:
        try:
            encoded_url = urllib.parse.quote_plus(url)
            query = 'https://shot.screenshotapi.net/screenshot'
            query += f'?token={self.api_token}&url={encoded_url}&output=image&file_type=png'

            with urllib.request.urlopen(query) as response:
                screenshot_data = BytesIO(response.read())
                screenshot_data.seek(0)
                return screenshot_data

        except Exception as e:
            raise e

    @screenshot.command(name="list", aliases=["ls"])
    async def _list(self, ctx: commands.Context) -> None:
        if not self._is_administrator(ctx):
            await ctx.reply("You need the Administrator permission to use this command.")
            return

        async with self.bot.pool.acquire() as connection:

            grants = await connection.fetch(
                "SELECT * FROM ss_grants"
            )

            if not grants:
                await ctx.reply("No permissions granted.")
                return

            embed = (
                Embed(
                    title="Users with screenshot permissions",
                    description=(
                        f"{', '.join(f'<@{user["user_id"]}>' for user in grants[:20])} *(and {len(grants) - 20} more)*"
                        if len(grants) > 20
                        else ", ".join(f"<@{user['user_id']}>" for user in grants)
                    ),
                    color=0x2A2D30,
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
            await ctx.reply("You need the Administrator permission to use this command.")
            return

        async with self.bot.pool.acquire() as connection:
            granted = await connection.fetch(
                "SELECT * FROM ss_grants WHERE user_id = $1",
                user.id,
            )

            if granted:
                await ctx.reply(f"{user.mention} already has permissions.")
                return

            await connection.execute(
                "INSERT INTO ss_grants VALUES ($1, $2)",
                user.id,
                ctx.author.id,
            )

            await ctx.reply(f"Granted {user.mention} permissions.")

    @screenshot.command(name="revoke")
    async def revoke(self, ctx: commands.Context, user: User) -> None:
        if not self._is_administrator(ctx):
            await ctx.reply("You need the Administrator permission to use this command.")
            return

        async with self.bot.pool.acquire() as connection:
            revoked = await connection.fetch(
                "SELECT * FROM ss_grants WHERE user_id = $1",
                user.id,
            )

            if not revoked:
                await ctx.reply(f"{user.mention} does not have permissions.")
                return

            await connection.execute(
                "DELETE FROM ss_grants WHERE user_id = $1",
                user.id,
            )

            await ctx.reply(f"Revoked {user.mention} permissions.")

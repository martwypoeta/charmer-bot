import secrets
import string

from discord import Forbidden, HTTPException
from discord.ext import commands


class Password(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["pass", "pw"])
    async def password(self, ctx: commands.Context, *, length: int = 16) -> None:
        if length > 64:
            await ctx.reply("The maximum length is 64.")
            return

        alphabet = string.ascii_letters + string.digits + "-_"

        password = "".join(secrets.choice(alphabet) for _ in range(length))

        try:
            await ctx.author.send(f"🔑 ||{password}||")
        except HTTPException, Forbidden:
            await ctx.reply("Open your DMs and try again.")
        finally:
            await ctx.message.add_reaction("📨")

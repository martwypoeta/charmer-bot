from discord import Embed
from discord.ext import commands

from bot.client import Bot


class Help(commands.Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @commands.command()
    async def help(self, ctx: commands.Context) -> None:
        all_command_count = sum(
            len(_commands) for _commands in self.bot.command_groups.values()
        )

        embed = (
            Embed(
                title="Commands",
                description="\n".join(
                    (f"Bot uptime: <t:{int(self.bot.boot.timestamp())}:R>",)
                ),
                color=0x2A2D30,
            )
            .set_author(
                name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url
            )
            .set_footer(text=f"{all_command_count} command(s) available")
        )

        for category, _commands in self.bot.command_groups.items():
            command_list = ", ".join(f"{command['name']}" for command in _commands)
            embed.add_field(
                name=f"{category.title()}",
                value=command_list if command_list else "No commands available",
                inline=False,
            )

        await ctx.reply(embed=embed)

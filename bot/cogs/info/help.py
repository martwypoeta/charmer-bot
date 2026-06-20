from discord import Member, User
from discord.ext import commands
from discord.ui import Container, LayoutView, Section, Separator, TextDisplay, Thumbnail

from bot.client import Bot, CommandInfo


class HelpLayout(LayoutView):
    def __init__(
        self,
        bot: Bot,
        author: User | Member,
        command_groups: dict[str, list[CommandInfo]],
    ) -> None:
        super().__init__(timeout=None)

        all_command_count = sum(len(commands) for commands in command_groups.values())
        boot_ts = int(bot.boot.timestamp())

        children: list = [
            Section(
                f"## Commands\n"
                f"-# Requested by {author.display_name}\n\n"
                f"**Uptime** — <t:{boot_ts}:R>",
                accessory=Thumbnail(
                    author.display_avatar.url,
                    description=author.display_name,
                ),
            ),
        ]

        for category, category_commands in command_groups.items():
            command_list = ", ".join(
                f"`{command['name']}`" for command in category_commands
            )
            children.append(Separator(visible=True))
            children.append(
                TextDisplay(
                    f"**{category.title()}** — "
                    f"{command_list or '_No commands available_'}"
                )
            )

        children.append(TextDisplay(f"-# {all_command_count} command(s) available"))

        self.add_item(Container(*children))


class Help(commands.Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @commands.command()
    async def help(self, ctx: commands.Context) -> None:
        await ctx.reply(view=HelpLayout(self.bot, ctx.author, self.bot.command_groups))

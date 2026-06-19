from discord import Embed, Member, NotFound
from discord import User as DiscordUser
from discord.ext import commands

from bot.client import Bot


class User(commands.Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @commands.command(aliases=["ui", "userinfo", "whois"])
    async def user(
        self, ctx: commands.Context, user: DiscordUser | Member | None = None
    ) -> None:
        if ctx.guild is None:
            await ctx.reply("This command can only be used in a server.")
            return

        user = user or ctx.author
        _user = await self.bot.fetch_user(user.id)

        try:
            member = await ctx.guild.fetch_member(user.id)
        except NotFound:
            member = None

        embed = (
            Embed(title="User Info", color=0x2A2D30)
            .set_author(name=user.name, icon_url=user.display_avatar.url)
            .add_field(
                name="Created at",
                value=f"<t:{int(user.created_at.timestamp())}:R>",
            )
            .set_thumbnail(url=user.display_avatar.url)
            .set_image(url=_user.banner.url if _user.banner else None)
            .set_footer(text=f"User ID: {user.id}")
        )

        if member and member.joined_at:
            embed.add_field(
                name="Joined at",
                value=f"<t:{int(member.joined_at.timestamp())}:R>",
            )

        embed.add_field(
            name="Names", value=f"{user.display_name} ({user.name})", inline=False
        )

        if member:
            roles = sorted(
                (role for role in member.roles if role != ctx.guild.default_role),
                reverse=True,
            )
            shown = " ".join(role.mention for role in roles[:3])
            if len(roles) > 3:
                shown += f" *(+{len(roles) - 3} more)*"
            embed.add_field(name="Roles", value=shown or "*none*", inline=False)

        links = {
            "Avatar": user.display_avatar.url,
            "Banner": _user.banner.url if _user.banner else None,
            "Profile": f"https://discord.com/users/{user.id}",
        }
        embed.add_field(
            name="Links",
            value="\n".join(
                f"- [{name} URL]({url})" for name, url in links.items() if url
            ),
            inline=False,
        )

        await ctx.reply(embed=embed)

from discord import Embed, User
from discord.ext import commands

from bot.client import Bot


class User(commands.Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @commands.command(aliases=["ui", "userinfo", "whois"])
    async def user(self, ctx: commands.Context, user: User = None) -> None:
        if user is None:
            user = ctx.author

        _user = await self.bot.fetch_user(user.id)

        embed = (
            Embed(
                title="User Info",
                color=0x2A2D30,
            )
            .set_author(
                name=user.name,
                icon_url=user.display_avatar.url,
            )
            .add_field(
                name="Created at",
                value=f"<t:{int(user.created_at.timestamp())}:R>",
            )
            .set_thumbnail(url=user.display_avatar.url)
            .set_image(url=_user.banner.url if _user.banner else None)
            .set_footer(text=f"User ID: {user.id}")
        )

        try:
            member = await ctx.guild.fetch_member(user.id)
        except Exception:
            member = None

        if member:
            embed.add_field(
                name="Joined at",
                value=f"<t:{int(member.joined_at.timestamp())}:R>",
            )

        embed.add_field(
            name="Names", value=f"{user.display_name} ({user.name})", inline=False
        )

        if member:
            embed.add_field(
                name="Roles",
                value=" ".join(
                    (
                        role.mention
                        for role in sorted(member.roles, reverse=True)[:3]
                        if role != ctx.guild.default_role
                    )
                )
                      + (
                          f" *(+{len(member.roles) - 3} more)*"
                          if len(member.roles) > 3
                          else ""
                      ),
                inline=False,
            )

        embed.add_field(
            name="Links",
            value=(
                "\n".join(
                    (
                        f"- [{name} URL]({url})"
                        for name, url in {
                        "Avatar": user.display_avatar.url,
                        "Banner": _user.banner.url if _user.banner else None,
                        "Profile": f"https://discord.com/users/{user.id}",
                    }.items()
                        if url
                    )
                )
            ),
            inline=False,
        )

        await ctx.reply(embed=embed)

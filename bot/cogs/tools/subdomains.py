import re

import aiohttp
from discord import Embed
from discord.ext import commands


class Subdomains(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["sub", "subdomain"])
    async def subdomains(self, ctx: commands.Context, *, domain: str) -> None:
        await ctx.typing()

        pattern = r"([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}"
        regex = re.compile(pattern)

        if not regex.fullmatch(domain):
            await ctx.reply("Invalid domain.")
            return

        domain = re.sub(r"^https?://", "", domain.lower())

        timeout = aiohttp.ClientTimeout(total=10)

        try:
            async with (
                aiohttp.ClientSession(timeout=timeout) as session,
                session.get(f"https://crt.sh/?q=%25.{domain}&output=json") as response,
            ):
                if response.status == 400:
                    await ctx.reply("Invalid URL.")
                    return
                elif response.status == 403:
                    await ctx.reply("API rate limit exceeded.")
                    return

                data = await response.json()
        except TimeoutError:
            await ctx.reply("Request timed out.")
            return
        except aiohttp.ClientError:
            await ctx.reply("Request failed.")

        subdomains = list(
            {
                item["common_name"]
                for item in data
                if not item["common_name"].startswith("*.")
                and item["common_name"].endswith(domain)
            }
        )

        subdomains.sort(key=len, reverse=True)

        display_limit = 15
        if len(subdomains) > display_limit:
            visible_subdomains = subdomains[:display_limit]
            more_count = len(subdomains) - display_limit
            more_line = f"\n- +{more_count} more domains"
        else:
            visible_subdomains = subdomains
            more_line = ""

        embed = (
            Embed(title=f"{domain} subdomains", color=0x2A2D30)
            .set_author(
                name=ctx.author.display_name,
                icon_url=ctx.author.display_avatar.url,
            )
            .set_footer(text=f"{len(subdomains)} subdomain(s) found")
        )
        embed.description = "- " + "\n- ".join(visible_subdomains) + more_line

        await ctx.reply(embed=embed)

import re
from urllib.parse import quote

import aiohttp
from discord import Member, User
from discord.ext import commands
from discord.ui import (
    ActionRow,
    Container,
    LayoutView,
    Section,
    Separator,
    TextDisplay,
    Thumbnail,
)

from bot.lib import paginate


class SubdomainsLayout(LayoutView):
    def __init__(
        self,
        domain: str,
        author: User | Member,
        page_items: list[str],
        page: int,
        pages: int,
        total: int,
        *,
        nav: ActionRow | None = None,
    ) -> None:
        super().__init__(timeout=None)

        search_url = f"https://hackertarget.com/hostsearch/?q={quote(domain)}"
        header = (
            f"## [{domain} subdomains]({search_url})\n"
            f"-# Requested by {author.display_name}"
        )
        summary = f"**{total}** subdomain(s) found"

        if page_items:
            list_text = "\n".join(f"- [{sub}](https://{sub})" for sub in page_items)
        else:
            list_text = "_No subdomains found._"

        children: list = [
            Section(
                f"{header}\n\n{summary}",
                accessory=Thumbnail(
                    author.display_avatar.url,
                    description=author.display_name,
                ),
            ),
            Separator(visible=True),
            TextDisplay(list_text),
        ]
        if pages > 1:
            children.append(TextDisplay(f"-# Page {page}/{pages}"))
        if nav is not None:
            children.append(nav)

        container = Container(*children)
        self.add_item(container)


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
                session.get(
                    f"https://api.hackertarget.com/hostsearch/?q={quote(domain)}"
                ) as response,
            ):
                if response.status == 400:
                    await ctx.reply("Invalid URL.")
                    return
                if response.status == 403:
                    await ctx.reply("API rate limit exceeded.")
                    return

                text = await response.text()
        except TimeoutError:
            await ctx.reply("Request timed out.")
            return
        except aiohttp.ClientError:
            await ctx.reply("Request failed.")
            return

        if text.startswith("error "):
            await ctx.reply("Invalid domain or search parameter.")
            return

        subdomains = list(
            {
                parts[0]
                for line in text.splitlines()
                if (parts := line.split(",", 1))
                and len(parts) == 2
                and parts[0].endswith(domain)
            }
        )

        subdomains.sort(key=len, reverse=True)

        def build_page(
            page_items: list[str], page: int, pages: int, nav: ActionRow | None
        ) -> LayoutView:
            return SubdomainsLayout(
                domain,
                ctx.author,
                page_items,
                page,
                pages,
                len(subdomains),
                nav=nav,
            )

        await paginate(ctx, subdomains, build_page, per_page=15)

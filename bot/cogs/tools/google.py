import aiohttp
from bs4 import BeautifulSoup

from discord import Embed
from discord.ext import commands


class Google(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def fetch_page(self, session, url):
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/117.0"
        }

        async with session.get(url, headers=headers) as response:
            return await response.text()

    async def get_search_results(self, query):
        results = []
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}&num=5"

        async with aiohttp.ClientSession() as session:
            html = await self.fetch_page(session, search_url)
            soup = BeautifulSoup(html, "html.parser")

            for result in soup.select(".tF2Cxc"):
                title = result.select_one(".DKV0Md").text
                link = result.select_one(".yuRUbf a")["href"]

                try:
                    snippet = result.select_one(".VwiC3b").text
                except Exception:
                    snippet = None

                results.append({"title": title, "link": link, "snippet": snippet})

        return results

    @commands.command()
    async def google(self, ctx: commands.Context, *, query: str) -> None:
        await ctx.typing()

        try:
            results = await self.get_search_results(query)

            embed = Embed(
                title="Google Search",
                color=0x2A2D30,
            ).set_author(
                name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url
            )

            for result in results:
                embed.add_field(
                    name=result["title"],
                    value=f"{result['snippet']}\n[Link]({result['link']})",
                    inline=False,
                )

            await ctx.reply(embed=embed)
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

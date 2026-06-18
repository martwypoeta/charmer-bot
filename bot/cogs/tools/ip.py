import re

import aiohttp
from discord import Embed
from discord.ext import commands


class Ip(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["ipv4"])
    async def ip(self, ctx: commands.Context, *, ip_or_domain: str) -> None:
        pattern = r"""
        (
            # IPv4 pattern
            (?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}
            (?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)
        |
            # IPv6 pattern
            (
                (?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}
                |(?:[0-9a-fA-F]{1,4}:){1,7}:
                |(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}
                |(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}
                |(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}
                |(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}
                |(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}
                |[0-9a-fA-F]{1,4}:(?::[0-9a-fA-F]{1,4}){1,6}
                |:(?::[0-9a-fA-F]{1,4}){1,7}|::
            )
        )
        """

        regex = re.compile(pattern, re.VERBOSE)

        if not regex.fullmatch(ip_or_domain):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                            f"https://dns.google/resolve?name={ip_or_domain}&type=A"
                    ) as resp:
                        if resp.status == 200:
                            dns_data = await resp.json()
                            if "Answer" in dns_data:
                                ip_address = dns_data["Answer"][0]["data"]
                            else:
                                await ctx.reply(
                                    f"Could not resolve the domain: {ip_or_domain}"
                                )
                                return
                        else:
                            await ctx.reply(
                                f"DNS resolution failed for: {ip_or_domain}"
                            )
                            return
            except aiohttp.ClientError:
                await ctx.reply(
                    f"An error occurred while resolving the domain: {ip_or_domain}"
                )
                return
        else:
            ip_address = ip_or_domain

        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f"http://ip-api.com/json/{ip_address}",
                    headers={"Accept": "application/json"},
            ) as response:
                if response.status != 200:
                    await ctx.reply("IP address not found.")
                    return

                data = await response.json()

        embed = (
            Embed(
                title="IP Lookup",
                url=f"https://whatismyipaddress.com/ip/{data['query']}",
                color=0x2A2D30,
            )
            .set_author(
                name=ctx.author.display_name,
                icon_url=ctx.author.display_avatar.url,
            )
            .add_field(name="IP", value=data["query"], inline=False)
            .add_field(
                name="Country",
                value=f":flag_{data['countryCode'].lower()}: {data['country']}",
            )
            .add_field(name="Region", value=data["regionName"])
            .add_field(name="City", value=data["city"])
            .add_field(name="ISP", value=data["isp"])
            .add_field(name="Timezone", value=data["timezone"])
            .add_field(name="ASN", value=data["as"])
            .set_footer(text=f"Latitude: {data['lat']} • Longitude: {data['lon']}")
        )

        await ctx.reply(embed=embed)

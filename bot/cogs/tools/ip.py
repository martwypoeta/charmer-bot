import re

import aiohttp
from discord import ButtonStyle, Member, SeparatorSpacing, User
from discord.ext import commands
from discord.ui import (
    ActionRow,
    Button,
    Container,
    LayoutView,
    Section,
    Separator,
    TextDisplay,
    Thumbnail,
)


class IpLookupLayout(LayoutView):
    def __init__(
        self,
        data: dict,
        author: User | Member,
        *,
        resolved_domain: str | None = None,
    ) -> None:
        super().__init__(timeout=None)

        ip = data["query"]
        country_code = data["countryCode"].lower()
        flag = f":flag_{country_code}:"
        maps_url = f"https://www.google.com/maps?q={data['lat']},{data['lon']}"
        details_url = f"https://whatismyipaddress.com/ip/{ip}"

        header = f"## [IP Lookup]({details_url})\n-# Requested by {author.display_name}"
        if resolved_domain:
            ip_line = f"Resolved `{resolved_domain}` → `{ip}`"
        else:
            ip_line = f"**`{ip}`**"

        location = f"{flag} **{data['city']}, {data['regionName']}**\n{data['country']}"
        network = (
            f"**ISP** — {data['isp']}\n"
            f"**ASN** — {data['as']}\n"
            f"**Timezone** — {data['timezone']}\n"
            f"**Coordinates** — `{data['lat']}, {data['lon']}`"
        )

        container = Container(
            Section(
                f"{header}\n\n{ip_line}",
                accessory=Thumbnail(
                    f"https://flagcdn.com/w320/{country_code}.png",
                    description=data["country"],
                ),
            ),
            Separator(visible=True),
            TextDisplay(location),
            Separator(visible=True, spacing=SeparatorSpacing.small),
            TextDisplay(network),
            ActionRow(
                Button(label="IP Details", url=details_url, style=ButtonStyle.link),
                Button(label="Google Maps", url=maps_url, style=ButtonStyle.link),
            ),
        )
        self.add_item(container)


class Ip(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["ipv4"])
    async def ip(self, ctx: commands.Context, *, ip_or_domain: str) -> None:
        await ctx.typing()

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
        resolved_domain: str | None = None
        timeout = aiohttp.ClientTimeout(total=10)

        if not regex.fullmatch(ip_or_domain):
            resolved_domain = ip_or_domain
            try:
                async with (
                    aiohttp.ClientSession(timeout=timeout) as session,
                    session.get(
                        f"https://dns.google/resolve?name={ip_or_domain}&type=A"
                    ) as resp,
                ):
                    if resp.status != 200:
                        await ctx.reply(f"DNS resolution failed for: {ip_or_domain}")
                        return

                    dns_data = await resp.json()
                    if "Answer" not in dns_data:
                        await ctx.reply(f"Could not resolve the domain: {ip_or_domain}")
                        return

                    ip_address = dns_data["Answer"][0]["data"]
            except aiohttp.ClientError:
                await ctx.reply(
                    f"An error occurred while resolving the domain: {ip_or_domain}"
                )
                return
        else:
            ip_address = ip_or_domain

        async with (
            aiohttp.ClientSession(timeout=timeout) as session,
            session.get(
                f"http://ip-api.com/json/{ip_address}",
                headers={"Accept": "application/json"},
            ) as response,
        ):
            if response.status != 200:
                await ctx.reply("IP address not found.")
                return

            data = await response.json()

        await ctx.reply(
            view=IpLookupLayout(
                data,
                ctx.author,
                resolved_domain=resolved_domain,
            )
        )

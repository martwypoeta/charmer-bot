from collections.abc import Callable
from typing import Any, cast

from discord import ButtonStyle, Embed, Interaction, Message
from discord.ext import commands
from discord.ui import Button, View


def _chunk[T](items: list[T], size: int) -> list[list[T]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


class _PaginatorView(View):
    def __init__(
        self,
        embeds: list[Embed],
        author_id: int,
        *,
        timeout: float = 30,
    ) -> None:
        super().__init__(timeout=timeout)
        self.embeds = embeds
        self.author_id = author_id
        self.page = 0
        self.message: Message | None = None

        self.prev = Button(label="◀", style=ButtonStyle.secondary)
        self.next = Button(label="▶", style=ButtonStyle.secondary)
        self.prev.callback = cast(Any, self._prev)
        self.next.callback = cast(Any, self._next)
        self.add_item(self.prev)
        self.add_item(self.next)
        self._update_buttons()

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "You can't interact with this pagination.", ephemeral=True
            )
            return False
        return True

    def _update_buttons(self) -> None:
        self.prev.disabled = self.page == 0
        self.next.disabled = self.page == len(self.embeds) - 1

    async def _turn(self, interaction: Interaction, delta: int) -> None:
        self.page += delta
        self._update_buttons()
        await interaction.response.edit_message(
            embed=self.embeds[self.page], view=self
        )

    async def _prev(self, interaction: Interaction) -> None:
        await self._turn(interaction, -1)

    async def _next(self, interaction: Interaction) -> None:
        await self._turn(interaction, 1)

    async def on_timeout(self) -> None:
        self.prev.disabled = True
        self.next.disabled = True
        if self.message:
            await self.message.edit(view=self)


class Pagination:
    @staticmethod
    async def send[T](
        ctx: commands.Context,
        items: list[T],
        embed_factory: Callable[[list[T], int, int], Embed],
        *,
        per_page: int = 15,
        timeout: float = 30,
    ) -> None:
        chunks = _chunk(items, per_page)
        pages = len(chunks)
        embeds = [embed_factory(chunk, i + 1, pages) for i, chunk in enumerate(chunks)]

        if len(embeds) == 1:
            await ctx.reply(embed=embeds[0])
            return

        view = _PaginatorView(embeds, ctx.author.id, timeout=timeout)
        view.message = await ctx.reply(embed=embeds[0], view=view)

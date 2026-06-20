from collections.abc import Callable
from itertools import batched
from typing import Any, cast

from discord import ButtonStyle, Interaction, Message
from discord.ext import commands
from discord.ui import ActionRow, Button, LayoutView

type PageBuilder[T] = Callable[[list[T], int, int, ActionRow | None], LayoutView]


def _chunk[T](items: list[T], size: int) -> list[list[T]]:
    return [list(batch) for batch in batched(items, size, strict=False)]


class _PaginatorView(LayoutView):
    def __init__(
        self,
        chunks: list[list],
        build_page: PageBuilder,
        author_id: int,
        *,
        timeout: float = 30,
    ) -> None:
        super().__init__(timeout=timeout)
        self._chunks = chunks
        self._build_page = build_page
        self._author_id = author_id
        self._page = 0
        self._page_count = len(chunks)
        self.message: Message | None = None
        self._render()

    def _nav_row(self, *, disabled: bool = False) -> ActionRow:
        prev = Button(
            label="◀",
            style=ButtonStyle.secondary,
            disabled=disabled or self._page == 0,
        )
        nxt = Button(
            label="▶",
            style=ButtonStyle.secondary,
            disabled=disabled or self._page >= self._page_count - 1,
        )
        prev.callback = cast(Any, self._prev_page)
        nxt.callback = cast(Any, self._next_page)
        return ActionRow(prev, nxt)

    def _render(self, *, disabled: bool = False) -> None:
        self.clear_items()
        layout = self._build_page(
            self._chunks[self._page],
            self._page + 1,
            self._page_count,
            self._nav_row(disabled=disabled),
        )
        for item in layout.children:
            self.add_item(item)

    async def _turn_page(self, interaction: Interaction, delta: int) -> None:
        if interaction.user.id != self._author_id:
            await interaction.response.send_message(
                "You can't interact with this pagination.", ephemeral=True
            )
            return
        self._page += delta
        self._render()
        await interaction.response.edit_message(view=self)

    async def _prev_page(self, interaction: Interaction) -> None:
        await self._turn_page(interaction, -1)

    async def _next_page(self, interaction: Interaction) -> None:
        await self._turn_page(interaction, 1)

    async def on_timeout(self) -> None:
        self._render(disabled=True)
        if self.message:
            await self.message.edit(view=self)


async def paginate[T](
    ctx: commands.Context,
    items: list[T],
    build_page: PageBuilder[T],
    *,
    per_page: int = 15,
    timeout: float = 30,
) -> None:
    chunks = _chunk(items, per_page) if items else [[]]

    if len(chunks) == 1:
        await ctx.reply(view=build_page(chunks[0], 1, 1, None))
        return

    view = _PaginatorView(chunks, build_page, ctx.author.id, timeout=timeout)
    view.message = await ctx.reply(view=view)

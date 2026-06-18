import asyncio
import time

from discord import AllowedMentions
from discord.ext import commands, tasks

from bot.client import Bot


class Remind(commands.Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.check_reminders.start()

    @commands.command(name="remind", aliases=["remindme"])
    async def remind(
            self, ctx: commands.Context, time_input: str, *, message: str
    ):
        async with self.bot.pool.acquire() as connection:
            reminders = await connection.fetch(
                "SELECT * FROM reminders WHERE user_id = $1",
                ctx.author.id,
            )
            if len(reminders) >= 2:
                await ctx.send(
                    "You have already set 2 reminders. Please delete one before setting a new one."
                )
                return

        if len(message) > 300:
            await ctx.send("Message too long.")
            return

        user_id = ctx.author.id
        channel_id = ctx.channel.id

        time_value, time_unit = self.parse_time(time_input)
        if time_value is None:
            await ctx.send("Invalid time format. Use '2h', '30m', etc.")
            return

        remind_time = int(time_value * time_unit)

        remind_time_epoch = int(time.time()) + remind_time
        message_id = ctx.message.id

        if remind_time < 60:
            await ctx.reply("Cannot set reminder for less than 1 minute.")
            return

        if remind_time > 2592000:
            await ctx.reply("Cannot set reminder for more than 30 days.")
            return

        if remind_time <= 300:
            await ctx.send(
                f"Reminder set for {time_input}. I will remind you: `{message}`"
            )
            await asyncio.sleep(remind_time)
            await self.send_reminder(user_id, message, channel_id)
            return

        async with self.bot.pool.acquire() as connection:
            await connection.execute(
                """
                INSERT INTO reminders (user_id, message_id, channel_id, message, remind_time)
                VALUES ($1, $2, $3, $4, $5)
                """,
                user_id,
                message_id,
                channel_id,
                message,
                remind_time_epoch,
            )

        await ctx.send(f"Reminder set for {time_input}. I will remind you: `{message}`")

    @tasks.loop(minutes=5)
    async def check_reminders(self):
        current_time = int(time.time())
        async with self.bot.pool.acquire() as connection:
            five_minutes = current_time + 300
            reminders = await connection.fetch(
                "SELECT * FROM reminders WHERE remind_time <= $1",
                five_minutes,
            )

        for reminder in reminders:
            time_to_go = reminder["remind_time"] - current_time

            async with self.bot.pool.acquire() as connection:
                await connection.execute(
                    "DELETE FROM reminders WHERE message_id = $1",
                    reminder["message_id"],
                )

            if time_to_go <= 0:
                await self.send_reminder(
                    reminder["user_id"], reminder["message"], reminder["channel_id"]
                )
                return

            await asyncio.sleep(time_to_go)
            await self.send_reminder(
                reminder["user_id"], reminder["message"], reminder["channel_id"]
            )

    async def send_reminder(self, user_id: int, message: str, channel_id: int):
        channel = await self.bot.fetch_channel(channel_id)
        if channel:
            await channel.send(
                f"## 🔔 Reminder\n<@{user_id}>: `{message}`",
                allowed_mentions=AllowedMentions(users=True),
            )

    def parse_time(self, time_input: str):
        time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        time_value = "".join(filter(str.isdigit, time_input))
        time_unit = time_input[-1]

        if time_value.isdigit() and time_unit in time_units:
            return int(time_value), time_units[time_unit]
        return None, None

    @check_reminders.before_loop
    async def before_check_reminders(self):
        await self.bot.wait_until_ready()

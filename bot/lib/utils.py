from discord.ext import commands


async def add_cogs(bot: commands.Bot, cogs: tuple[str, ...]) -> None:
    for cog_path in cogs:
        try:
            module = __import__(cog_path, fromlist=[""])
            cog_class_name = cog_path.split(".")[-1].title()
            cog_class = getattr(module, cog_class_name)
            await bot.add_cog(cog_class(bot))
        except (ImportError, AttributeError) as e:
            print(f"Failed to add cog '{cog_path}': {e}")
        except Exception as e:
            print(f"Unexpected error occurred when adding cog '{cog_path}': {e}")

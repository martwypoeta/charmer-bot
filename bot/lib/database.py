import os
from pathlib import Path

import aiofiles
from asyncpg import Pool
from asyncpg import create_pool as create_asyncpg_pool


async def create_pool() -> Pool:
    dsn = os.getenv("DATABASE_DSN")
    pool = await create_asyncpg_pool(dsn, min_size=10, max_size=30)

    schema_path = Path("bot/schema.sql")
    async with pool.acquire() as connection:
        async with aiofiles.open(schema_path, mode="r") as file:
            schema = await file.read()

        await connection.execute(schema)

    return pool

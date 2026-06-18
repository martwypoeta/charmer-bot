import os
from pathlib import Path

import aiofiles
from psycopg_pool import AsyncConnectionPool


async def create_pool() -> AsyncConnectionPool:
    pool = AsyncConnectionPool(
        os.environ["DATABASE_URL"], min_size=10, max_size=30, open=False
    )
    await pool.open()

    schema_path = Path("bot/schema.sql")
    async with pool.connection() as connection:
        async with aiofiles.open(schema_path) as file:
            schema = await file.read()

        await connection.execute(schema)

    return pool

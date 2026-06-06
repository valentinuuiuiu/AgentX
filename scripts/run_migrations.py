"""Enhanced database migrations and seeding for Rehoboam platform.

Usage:
    python scripts/run_migrations.py seed          # Seed with realistic data
    python scripts/run_migrations.py check           # Check DB connectivity
"""
import asyncio
import os
import sys
import asyncpg
import logging

# Ensure project root on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.db_seeds import seed_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migrations")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://rehoboam:rehoboam123@postgres:5432/rehoboam",
)


async def check_db():
    try:
        pool = await asyncpg.create_pool(DATABASE_URL, command_timeout=5)
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT version() as v")
            logger.info(f"DB connected: {row['v']}")
            # List tables
            tables = await conn.fetch(
                "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"
            )
            logger.info(f"Tables: {[t['tablename'] for t in tables]}")
        await pool.close()
        return True
    except Exception as e:
        logger.error(f"DB check failed: {e}")
        return False


async def run_seed():
    pool = await asyncpg.create_pool(DATABASE_URL, command_timeout=10)
    try:
        result = await seed_database(pool)
        logger.info(f"Seed result: {result}")
    finally:
        await pool.close()


async def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_migrations.py [seed|check]")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "check":
        ok = await check_db()
        sys.exit(0 if ok else 1)
    elif cmd == "seed":
        await run_seed()
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

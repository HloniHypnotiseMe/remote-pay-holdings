#!/usr/bin/env python3
"""
C6 Web Department — Database Connection Helper
Wraps asyncpg pool for the FastAPI server.
"""
import os
import asyncpg
from pathlib import Path
from typing import Optional


class Database:
    """Async Postgres pool wrapper."""

    def __init__(self, dsn: Optional[str] = None):
        self.dsn = dsn or self._load_dsn()
        self.pool: Optional[asyncpg.Pool] = None

    def _load_dsn(self) -> str:
        """Load DATABASE_URL from .env or env vars."""
        # First, try to read from .env
        env_path = Path(__file__).resolve().parents[2] / ".env"
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("DATABASE_URL="):
                    return line.split("=", 1)[1].strip()

        # Fallback to env var
        dsn = os.environ.get("DATABASE_URL")
        if dsn:
            return dsn

        raise RuntimeError(
            "DATABASE_URL not found. Create .env with DATABASE_URL=..."
        )

    async def connect(self):
        """Create the connection pool."""
        self.pool = await asyncpg.create_pool(
            self.dsn, min_size=1, max_size=10
        )
        return self.pool

    async def disconnect(self):
        """Close the pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None

    async def acquire(self):
        """Get a connection from the pool."""
        if not self.pool:
            await self.connect()
        return self.pool.acquire()

    async def health_check(self):
        """Ping the DB and return basic stats."""
        if not self.pool:
            await self.connect()
        async with self.pool.acquire() as conn:
            version = await conn.fetchval("SELECT version()")
            tables = await conn.fetch(
                "SELECT tablename FROM pg_tables "
                "WHERE schemaname = 'public' ORDER BY tablename"
            )
            return {
                "connected": True,
                "version": version.split(",")[0],
                "table_count": len(tables),
                "tables": [t["tablename"] for t in tables],
            }


if __name__ == "__main__":
    import asyncio

    async def main():
        db = Database()
        print("Database helper ready")
        try:
            health = await db.health_check()
            print(f"Connected: {health['connected']}")
            print(f"Version: {health['version']}")
            print(f"Tables: {health['table_count']}")
            print(f"Table names: {', '.join(health['tables'][:5])}...")
        except Exception as e:
            print(f"Connection failed: {e}")
        finally:
            await db.disconnect()

    asyncio.run(main())

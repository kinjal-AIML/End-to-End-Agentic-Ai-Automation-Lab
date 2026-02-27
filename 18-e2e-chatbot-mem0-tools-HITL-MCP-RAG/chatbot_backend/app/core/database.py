import logging
from psycopg_pool import AsyncConnectionPool # <--- Changed to Async
from app.core.config import settings

logger = logging.getLogger("uvicorn")

class Database:
    def __init__(self):
        self.pool = None

    async def connect(self): # <--- Made async
        try:
            # Create pool WITHOUT opening it immediately (kwargs open=False)
            self.pool = AsyncConnectionPool(
                conninfo=settings.DATABASE_URL, 
                max_size=20, 
                kwargs={"autocommit": True},
                open=False # <--- Add this
            )
            await self.pool.open() # <--- Open explicitly here
            logger.info("✅ Async Database connection pool created.")
        except Exception as e:
            logger.error(f"❌ DB Connection failed: {e}")
            raise e

    async def close(self): # <--- Made async
        if self.pool:
            await self.pool.close() # <--- Await close
            logger.info("🔻 Database connection pool closed.")

    def get_pool(self):
        if not self.pool:
            raise Exception("Database not connected")
        return self.pool

db = Database()
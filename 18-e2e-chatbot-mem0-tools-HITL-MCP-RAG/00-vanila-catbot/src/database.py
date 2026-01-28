import os
import asyncio
from psycopg_pool import AsyncConnectionPool
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("LANG_DB", "")

encoded_password = quote_plus(DB_PASSWORD)
DATABASE_URL = f"postgresql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=disable"

# Global Pool (Closed initially)
pool = AsyncConnectionPool(
    conninfo=DATABASE_URL, 
    max_size=20, 
    kwargs={"autocommit": True}, 
    open=False 
)

async def ensure_custom_tables():
    """Creates the metadata table for sidebar history."""
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS chat_metadata (
                    thread_id TEXT PRIMARY KEY,
                    title TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

async def save_thread_title(thread_id, title):
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO chat_metadata (thread_id, title) VALUES (%s, %s) ON CONFLICT (thread_id) DO UPDATE SET title = %s",
                (str(thread_id), title, title)
            )

async def get_all_threads():
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT thread_id, title FROM chat_metadata ORDER BY created_at DESC")
            rows = await cur.fetchall()
            return [{"id": r[0], "title": r[1]} for r in rows]
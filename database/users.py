"""
CRUD-операции для таблицы users.
"""

import logging
from typing import Optional
import aiosqlite
from .db import get_db

logger = logging.getLogger(__name__)


async def get_or_create_user(telegram_id: int, username: str = None, full_name: str = None) -> dict:
    """Возвращает пользователя из БД или создаёт нового."""
    async with get_db() as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON;")
        await db.execute(
            """
            INSERT INTO users (telegram_id, username, full_name)
            VALUES (?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                username    = excluded.username,
                full_name   = excluded.full_name,
                last_active = CURRENT_TIMESTAMP
            """,
            (telegram_id, username, full_name),
        )
        await db.commit()
        async with db.execute(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row)


async def get_user_by_telegram_id(telegram_id: int) -> Optional[dict]:
    async with get_db() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_all_users() -> list:
    async with get_db() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users") as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def is_blacklisted(telegram_id: int) -> bool:
    async with get_db() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT id FROM blacklist WHERE telegram_id = ?", (telegram_id,)
        ) as cursor:
            return await cursor.fetchone() is not None


async def add_to_blacklist(telegram_id: int, reason: str = None):
    async with get_db() as db:
        db.row_factory = aiosqlite.Row
        await db.execute(
            "INSERT OR IGNORE INTO blacklist (telegram_id, reason) VALUES (?, ?)",
            (telegram_id, reason),
        )
        await db.commit()


async def remove_from_blacklist(telegram_id: int):
    async with get_db() as db:
        db.row_factory = aiosqlite.Row
        await db.execute("DELETE FROM blacklist WHERE telegram_id = ?", (telegram_id,))
        await db.commit()


async def get_blacklist() -> list:
    async with get_db() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT bl.*, u.username, u.full_name
            FROM blacklist bl
            LEFT JOIN users u ON u.telegram_id = bl.telegram_id
            ORDER BY bl.added_at DESC
            """
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

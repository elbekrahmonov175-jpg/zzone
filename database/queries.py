"""
CRUD-операции для прайс-листа, акций, локации и статистики.
"""

import logging
from typing import Optional, List
from .db import get_db

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# ПРАЙС-ЛИСТ
# ──────────────────────────────────────────────

async def get_prices() -> List[dict]:
    """Возвращает все цены."""
    async with await get_db() as db:
        async with db.execute("SELECT * FROM prices ORDER BY id") as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def update_price(zone: str, price_hour: int):
    """Обновляет цену для зоны."""
    async with await get_db() as db:
        await db.execute(
            "UPDATE prices SET price_hour = ?, updated_at = CURRENT_TIMESTAMP WHERE zone = ?",
            (price_hour, zone),
        )
        await db.commit()


# ──────────────────────────────────────────────
# АКЦИИ
# ──────────────────────────────────────────────

async def get_active_promotions() -> List[dict]:
    """Возвращает активные акции."""
    async with await get_db() as db:
        async with db.execute(
            "SELECT * FROM promotions WHERE is_active = 1 ORDER BY created_at DESC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_all_promotions() -> List[dict]:
    """Возвращает все акции (включая неактивные) — для админ-панели."""
    async with await get_db() as db:
        async with db.execute(
            "SELECT * FROM promotions ORDER BY created_at DESC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_promotion_by_id(promo_id: int) -> Optional[dict]:
    async with await get_db() as db:
        async with db.execute(
            "SELECT * FROM promotions WHERE id = ?", (promo_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def create_promotion(title: str, description: str) -> int:
    async with await get_db() as db:
        cursor = await db.execute(
            "INSERT INTO promotions (title, description) VALUES (?, ?)",
            (title, description),
        )
        await db.commit()
        return cursor.lastrowid


async def update_promotion(promo_id: int, title: str, description: str, is_active: int):
    async with await get_db() as db:
        await db.execute(
            "UPDATE promotions SET title=?, description=?, is_active=? WHERE id=?",
            (title, description, is_active, promo_id),
        )
        await db.commit()


async def delete_promotion(promo_id: int):
    async with await get_db() as db:
        await db.execute("DELETE FROM promotions WHERE id = ?", (promo_id,))
        await db.commit()


# ──────────────────────────────────────────────
# ЛОКАЦИЯ
# ──────────────────────────────────────────────

async def get_location() -> Optional[dict]:
    """Возвращает данные о местоположении клуба."""
    async with await get_db() as db:
        async with db.execute("SELECT * FROM location LIMIT 1") as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def update_location(address: str, phone: str, telegram: str, lat: float, lon: float):
    """Обновляет данные локации."""
    async with await get_db() as db:
        await db.execute(
            """
            UPDATE location
            SET address=?, phone=?, telegram=?, latitude=?, longitude=?
            WHERE id = 1
            """,
            (address, phone, telegram, lat, lon),
        )
        await db.commit()


# ──────────────────────────────────────────────
# СТАТИСТИКА
# ──────────────────────────────────────────────

async def get_statistics() -> dict:
    """Собирает сводную статистику для админ-панели."""
    async with await get_db() as db:
        stats = {}

        # Пользователи
        async with db.execute("SELECT COUNT(*) FROM users") as c:
            stats["total_users"] = (await c.fetchone())[0]

        async with db.execute(
            "SELECT COUNT(*) FROM users WHERE DATE(created_at) = DATE('now')"
        ) as c:
            stats["new_users_today"] = (await c.fetchone())[0]

        async with db.execute(
            "SELECT COUNT(*) FROM users WHERE DATE(created_at) >= DATE('now', 'start of month')"
        ) as c:
            stats["users_this_month"] = (await c.fetchone())[0]

        # Брони
        for status in ("pending", "confirmed", "rejected", "cancelled"):
            async with db.execute(
                "SELECT COUNT(*) FROM bookings WHERE status = ?", (status,)
            ) as c:
                stats[f"bookings_{status}"] = (await c.fetchone())[0]

        async with db.execute("SELECT COUNT(*) FROM bookings") as c:
            stats["total_bookings"] = (await c.fetchone())[0]

        # Активные = pending + confirmed
        stats["active_bookings"] = (
            stats["bookings_pending"] + stats["bookings_confirmed"]
        )

        # Популярные зоны
        async with db.execute(
            """
            SELECT zone, COUNT(*) as cnt
            FROM bookings
            GROUP BY zone
            ORDER BY cnt DESC
            """
        ) as c:
            rows = await c.fetchall()
            stats["popular_zones"] = [dict(r) for r in rows]

        return stats

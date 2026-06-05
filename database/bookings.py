"""
CRUD-операции для таблицы bookings.
"""

import logging
from typing import Optional, List
from .db import get_db

logger = logging.getLogger(__name__)

STATUS_LABELS = {
    "pending":   "⏳ Ожидает подтверждения",
    "confirmed": "✅ Подтверждена",
    "rejected":  "❌ Отклонена",
    "cancelled": "🚫 Отменена",
}


async def create_booking(
    user_id: int,
    zone: str,
    booking_date: str,
    booking_time: str,
    duration: int,
) -> int:
    """Создаёт новую заявку на бронирование. Возвращает ID брони."""
    async with await get_db() as db:
        cursor = await db.execute(
            """
            INSERT INTO bookings (user_id, zone, booking_date, booking_time, duration)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, zone, booking_date, booking_time, duration),
        )
        await db.commit()
        return cursor.lastrowid


async def get_booking_by_id(booking_id: int) -> Optional[dict]:
    """Возвращает бронирование по ID."""
    async with await get_db() as db:
        async with db.execute(
            """
            SELECT b.*, u.telegram_id, u.username, u.full_name
            FROM bookings b
            JOIN users u ON u.id = b.user_id
            WHERE b.id = ?
            """,
            (booking_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_user_bookings(user_id: int, active_only: bool = False) -> List[dict]:
    """Возвращает все бронирования пользователя."""
    sql = """
        SELECT * FROM bookings
        WHERE user_id = ?
    """
    params = [user_id]

    if active_only:
        sql += " AND status IN ('pending', 'confirmed')"

    sql += " ORDER BY booking_date DESC, booking_time DESC"

    async with await get_db() as db:
        async with db.execute(sql, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_pending_bookings() -> List[dict]:
    """Возвращает все заявки со статусом 'pending' (для админ-панели)."""
    async with await get_db() as db:
        async with db.execute(
            """
            SELECT b.*, u.telegram_id, u.username, u.full_name
            FROM bookings b
            JOIN users u ON u.id = b.user_id
            WHERE b.status = 'pending'
            ORDER BY b.created_at ASC
            """
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_all_bookings() -> List[dict]:
    """Возвращает все бронирования (для статистики)."""
    async with await get_db() as db:
        async with db.execute(
            """
            SELECT b.*, u.telegram_id, u.username, u.full_name
            FROM bookings b
            JOIN users u ON u.id = b.user_id
            ORDER BY b.created_at DESC
            """
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def update_booking_status(
    booking_id: int,
    status: str,
    admin_comment: str = None,
) -> bool:
    """Обновляет статус бронирования."""
    async with await get_db() as db:
        await db.execute(
            """
            UPDATE bookings
            SET status = ?, admin_comment = ?
            WHERE id = ?
            """,
            (status, admin_comment, booking_id),
        )
        await db.commit()
        return True


async def cancel_booking(booking_id: int, user_id: int) -> bool:
    """
    Отменяет бронирование.
    Проверяет, что бронирование принадлежит пользователю.
    """
    async with await get_db() as db:
        result = await db.execute(
            """
            UPDATE bookings
            SET status = 'cancelled'
            WHERE id = ? AND user_id = ? AND status IN ('pending', 'confirmed')
            """,
            (booking_id, user_id),
        )
        await db.commit()
        return result.rowcount > 0


async def get_unreminded_upcoming_bookings() -> List[dict]:
    """
    Возвращает подтверждённые брони, до которых осталось ~30 минут,
    и по которым ещё не было отправлено напоминание.
    Используется планировщиком для уведомлений.
    """
    async with await get_db() as db:
        async with db.execute(
            """
            SELECT b.*, u.telegram_id, u.full_name
            FROM bookings b
            JOIN users u ON u.id = b.user_id
            WHERE b.status = 'confirmed'
              AND b.reminded = 0
              AND datetime(b.booking_date || ' ' || b.booking_time)
                  BETWEEN datetime('now', '+25 minutes')
                  AND     datetime('now', '+35 minutes')
            """,
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def mark_reminded(booking_id: int):
    """Помечает бронирование как «напоминание отправлено»."""
    async with await get_db() as db:
        await db.execute(
            "UPDATE bookings SET reminded = 1 WHERE id = ?", (booking_id,)
        )
        await db.commit()

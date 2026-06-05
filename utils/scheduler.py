"""
Планировщик задач для автоматических уведомлений.
Каждые 60 секунд проверяет брони, до которых осталось ~30 минут,
и отправляет напоминания пользователям.
"""

import asyncio
import logging

from aiogram import Bot
from database import get_unreminded_upcoming_bookings, mark_reminded
from utils.notifications import notify_reminder

logger = logging.getLogger(__name__)


async def reminders_loop(bot: Bot):
    """
    Фоновая задача: каждую минуту ищет брони, до которых ~30 минут,
    и шлёт напоминание, если ещё не отправляли.

    Важно: время в БД хранится в UTC, поэтому запросы используют
    datetime('now') которая тоже UTC. Если вы хотите работать
    в местном времени — конвертируйте при записи брони.
    """
    logger.info("⏰ Планировщик напоминаний запущен")
    while True:
        try:
            bookings = await get_unreminded_upcoming_bookings()
            for booking in bookings:
                telegram_id = booking["telegram_id"]
                logger.info(
                    "📨 Отправка напоминания пользователю %d (бронь #%d)",
                    telegram_id,
                    booking["id"],
                )
                await notify_reminder(bot, telegram_id, booking)
                await mark_reminded(booking["id"])
        except Exception as e:
            logger.error("Ошибка в планировщике напоминаний: %s", e)

        # Пауза 60 секунд между проверками
        await asyncio.sleep(60)

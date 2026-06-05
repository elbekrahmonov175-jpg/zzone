"""
Middleware для автоматической регистрации пользователей
и проверки чёрного списка при каждом обращении к боту.
"""

import logging
from typing import Any, Callable, Dict, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from database import get_or_create_user, is_blacklisted

logger = logging.getLogger(__name__)


class UserMiddleware(BaseMiddleware):
    """
    При каждом входящем сообщении/callback:
    1. Регистрирует пользователя в базе (или обновляет данные).
    2. Проверяет, не в чёрном ли он списке.
    3. Пробрасывает объект пользователя в data['db_user'].
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Определяем from_user в зависимости от типа события
        from_user = None
        if isinstance(event, Message):
            from_user = event.from_user
        elif isinstance(event, CallbackQuery):
            from_user = event.from_user

        if from_user and not from_user.is_bot:
            # Регистрируем / обновляем пользователя
            db_user = await get_or_create_user(
                telegram_id=from_user.id,
                username=from_user.username,
                full_name=from_user.full_name,
            )
            data["db_user"] = db_user

            # Логируем активность
            logger.info(
                "👤 Пользователь %s (%d) — %s",
                from_user.username or from_user.full_name,
                from_user.id,
                type(event).__name__,
            )

            # Проверяем чёрный список — блокируем только бронирование,
            # но не весь бот (проверка выполняется в handler'е бронирования)
            data["is_blacklisted"] = await is_blacklisted(from_user.id)
        else:
            data["db_user"] = None
            data["is_blacklisted"] = False

        return await handler(event, data)

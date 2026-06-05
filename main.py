"""
Точка входа в приложение.
Запускает бота в режиме polling и фоновый планировщик напоминаний.
"""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config.settings import settings
from database import init_db
from middlewares import UserMiddleware
from handlers import (
    common_router,
    booking_router,
    info_router,
    contact_router,
    admin_bookings_router,
    admin_manage_router,
    admin_broadcast_router,
)
from utils.scheduler import reminders_loop

# ──────────────────────────────────────────────
# НАСТРОЙКА ЛОГИРОВАНИЯ
# ──────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/bot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


async def main():
    """Основная функция запуска бота."""
    import os
    os.makedirs("logs", exist_ok=True)

    if not settings.BOT_TOKEN:
        logger.critical("BOT_TOKEN не задан! Проверьте файл .env")
        sys.exit(1)

    # Инициализируем базу данных
    await init_db()
    logger.info("База данных инициализирована")

    # Создаём объект бота
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # Создаём диспетчер
    dp = Dispatcher()

    # Подключаем middleware
    dp.message.middleware(UserMiddleware())
    dp.callback_query.middleware(UserMiddleware())

    # Регистрируем роутеры (порядок важен!)
    dp.include_router(common_router)
    dp.include_router(booking_router)
    dp.include_router(info_router)
    dp.include_router(contact_router)
    dp.include_router(admin_bookings_router)
    dp.include_router(admin_manage_router)
    dp.include_router(admin_broadcast_router)

    logger.info("🤖 Бот запускается...")
    logger.info("Администраторы: %s", settings.ADMIN_IDS)

    # Запускаем фоновый планировщик напоминаний
    asyncio.create_task(reminders_loop(bot))

    # Запускаем polling
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        logger.info("Бот остановлен.")


if __name__ == "__main__":
    asyncio.run(main())

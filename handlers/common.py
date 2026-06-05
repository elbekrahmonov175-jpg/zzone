"""
Обработчик команды /start и навигация по главному меню.
"""

import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart

from keyboards.user_kb import main_menu_kb

logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, db_user: dict):
    """Приветственное сообщение и главное меню."""
    name = message.from_user.first_name or "друг"
    await message.answer(
        f"👋 Привет, <b>{name}</b>!\n\n"
        "Добро пожаловать в <b>Computer Club Bot</b> 🎮\n\n"
        "Здесь вы можете:\n"
        "• Забронировать место\n"
        "• Узнать цены и акции\n"
        "• Связаться с администратором\n\n"
        "Выберите нужный пункт меню 👇",
        parse_mode="HTML",
        reply_markup=main_menu_kb(),
    )
    logger.info("Пользователь %d вошёл в бот", message.from_user.id)

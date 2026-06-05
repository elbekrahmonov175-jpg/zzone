"""
Хендлеры информационных разделов: прайс-лист, акции, локация.
"""

import logging
from aiogram import Router, F
from aiogram.types import Message

from database import get_prices, get_active_promotions, get_location
from keyboards.user_kb import main_menu_kb

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text == "💰 Прайс-лист")
async def show_prices(message: Message):
    """Показывает актуальный прайс-лист из базы данных."""
    prices = await get_prices()

    if not prices:
        await message.answer("Прайс-лист временно недоступен.", reply_markup=main_menu_kb())
        return

    zone_icons = {"Standard": "🖥", "VIP": "👑", "PS5": "🎮"}
    text = "💰 <b>Прайс-лист</b>\n\n"
    for p in prices:
        icon = zone_icons.get(p["zone"], "•")
        text += f"{icon} <b>{p['zone']}</b>: {p['price_hour']:,} сум/час\n"

    text += "\n💡 Уточняйте у администратора о пакетах и скидках."
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu_kb())


@router.message(F.text == "🎁 Акции")
async def show_promotions(message: Message):
    """Показывает активные акции."""
    promos = await get_active_promotions()

    if not promos:
        await message.answer(
            "😔 Сейчас активных акций нет.\nСледите за обновлениями!",
            reply_markup=main_menu_kb(),
        )
        return

    text = "🎁 <b>Текущие акции</b>\n\n"
    for p in promos:
        text += f"🔥 <b>{p['title']}</b>\n{p['description']}\n\n"

    await message.answer(text, parse_mode="HTML", reply_markup=main_menu_kb())


@router.message(F.text == "📍 Локация")
async def show_location(message: Message):
    """Показывает информацию о клубе и геолокацию."""
    loc = await get_location()

    if not loc:
        await message.answer("Информация о клубе временно недоступна.", reply_markup=main_menu_kb())
        return

    text = (
        "📍 <b>Наш клуб</b>\n\n"
        f"🏠 Адрес: {loc['address']}\n"
        f"📞 Телефон: {loc['phone']}\n"
        f"💬 Telegram: {loc['telegram']}\n\n"
        "Нажмите кнопку ниже, чтобы открыть карту 👇"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu_kb())

    # Отправляем геолокацию отдельным сообщением
    try:
        await message.bot.send_location(
            chat_id=message.chat.id,
            latitude=loc["latitude"],
            longitude=loc["longitude"],
        )
    except Exception as e:
        logger.warning("Не удалось отправить геолокацию: %s", e)

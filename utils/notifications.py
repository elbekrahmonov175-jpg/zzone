"""
Утилита для отправки уведомлений пользователям и администраторам.
"""

import logging
from aiogram import Bot
from config.settings import settings
from database import STATUS_LABELS

logger = logging.getLogger(__name__)


async def notify_admins(bot: Bot, text: str, **kwargs):
    """Отправляет сообщение всем администраторам из settings.ADMIN_IDS."""
    for admin_id in settings.ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text, **kwargs)
        except Exception as e:
            logger.warning("Не удалось отправить сообщение админу %d: %s", admin_id, e)


async def notify_user(bot: Bot, telegram_id: int, text: str, **kwargs) -> bool:
    """Отправляет сообщение пользователю. Возвращает True при успехе."""
    try:
        await bot.send_message(telegram_id, text, **kwargs)
        return True
    except Exception as e:
        logger.warning("Не удалось отправить сообщение пользователю %d: %s", telegram_id, e)
        return False


async def notify_new_booking(bot: Bot, booking: dict, user: dict):
    """Уведомляет администраторов о новой заявке."""
    from keyboards.admin_kb import booking_actions_kb

    text = (
        "🆕 <b>Новая заявка на бронирование!</b>\n\n"
        f"👤 Пользователь: {user.get('full_name', 'Неизвестно')}\n"
        f"🔗 @{user.get('username', '—')}\n"
        f"🆔 ID: <code>{user.get('telegram_id')}</code>\n\n"
        f"🎮 Зона: <b>{booking['zone']}</b>\n"
        f"📅 Дата: <b>{booking['booking_date']}</b>\n"
        f"⏰ Время: <b>{booking['booking_time']}</b>\n"
        f"⏱ Длительность: <b>{booking['duration']} ч.</b>\n"
        f"🔖 Заявка №{booking['id']}"
    )
    for admin_id in settings.ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                text,
                parse_mode="HTML",
                reply_markup=booking_actions_kb(booking["id"]),
            )
        except Exception as e:
            logger.warning("Ошибка уведомления админа %d: %s", admin_id, e)


async def notify_booking_status_changed(bot: Bot, booking: dict, telegram_id: int):
    """Уведомляет пользователя об изменении статуса брони."""
    status_label = STATUS_LABELS.get(booking["status"], booking["status"])
    comment = booking.get("admin_comment") or ""

    text = (
        f"📬 <b>Статус вашей заявки изменён</b>\n\n"
        f"🎮 Зона: {booking['zone']}\n"
        f"📅 {booking['booking_date']} {booking['booking_time']} ({booking['duration']} ч.)\n"
        f"Статус: {status_label}\n"
    )
    if comment:
        text += f"\n💬 Сообщение от администратора:\n{comment}"

    await notify_user(bot, telegram_id, text, parse_mode="HTML")


async def notify_booking_cancelled_to_admins(bot: Bot, booking: dict, user: dict):
    """Уведомляет администраторов об отмене брони пользователем."""
    text = (
        "🚫 <b>Пользователь отменил бронирование</b>\n\n"
        f"👤 {user.get('full_name', '—')} (@{user.get('username', '—')})\n"
        f"🆔 ID: <code>{user.get('telegram_id')}</code>\n\n"
        f"🎮 Зона: {booking['zone']}\n"
        f"📅 {booking['booking_date']} {booking['booking_time']} ({booking['duration']} ч.)\n"
        f"🔖 Заявка №{booking['id']}"
    )
    await notify_admins(bot, text, parse_mode="HTML")


async def notify_reminder(bot: Bot, telegram_id: int, booking: dict):
    """Отправляет напоминание пользователю за 30 минут до начала игры."""
    text = (
        "⏰ <b>Напоминание!</b>\n\n"
        f"До вашей игры осталось <b>30 минут</b>! Вы уже едете? 🚀\n\n"
        f"🎮 Зона: <b>{booking['zone']}</b>\n"
        f"📅 Дата: {booking['booking_date']}\n"
        f"🕐 Начало: <b>{booking['booking_time']}</b>\n"
        f"⏱ Длительность: {booking['duration']} ч.\n\n"
        "Ждём вас! 🎉"
    )
    await notify_user(bot, telegram_id, text, parse_mode="HTML")

"""
Административная панель — главное меню, управление заявками,
ответы пользователям с предложением другого времени.
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config.settings import settings
from database import (
    get_pending_bookings,
    get_booking_by_id,
    update_booking_status,
    get_user_by_telegram_id,
)
from keyboards.admin_kb import (
    admin_menu_kb,
    booking_actions_kb,
    back_to_bookings_kb,
    back_to_admin_kb,
)
from utils.notifications import notify_booking_status_changed

logger = logging.getLogger(__name__)
router = Router()


def admin_only(func):
    """Декоратор — проверяет, что вызывающий является администратором."""
    import functools

    @functools.wraps(func)
    async def wrapper(event, *args, **kwargs):
        user_id = event.from_user.id if hasattr(event, "from_user") else None
        if user_id not in settings.ADMIN_IDS:
            if hasattr(event, "answer"):
                await event.answer("🚫 Доступ запрещён.")
            return
        return await func(event, *args, **kwargs)

    return wrapper


# ──────────────────────────────────────────────
# FSM ДЛЯ "ПРЕДЛОЖИТЬ ДРУГОЕ ВРЕМЯ"
# ──────────────────────────────────────────────

class AdminBookingFSM(StatesGroup):
    propose_time_message = State()  # Ввод сообщения пользователю


# ──────────────────────────────────────────────
# ОТКРЫТИЕ АДМИН-ПАНЕЛИ
# ──────────────────────────────────────────────

@router.message(Command("admin"))
@admin_only
async def admin_panel(message: Message):
    await message.answer(
        "🔐 <b>Административная панель</b>\n\n"
        "Выберите раздел:",
        parse_mode="HTML",
        reply_markup=admin_menu_kb(),
    )
    logger.info("Администратор %d открыл панель", message.from_user.id)


@router.callback_query(F.data == "admin:menu")
@admin_only
async def admin_menu_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🔐 <b>Административная панель</b>\n\n"
        "Выберите раздел:",
        parse_mode="HTML",
        reply_markup=admin_menu_kb(),
    )
    await callback.answer()


# ──────────────────────────────────────────────
# СПИСОК НОВЫХ ЗАЯВОК
# ──────────────────────────────────────────────

@router.callback_query(F.data == "admin:bookings")
@admin_only
async def admin_show_bookings(callback: CallbackQuery):
    bookings = await get_pending_bookings()

    if not bookings:
        await callback.message.edit_text(
            "📭 Новых заявок нет.",
            reply_markup=back_to_admin_kb(),
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        f"📋 <b>Новые заявки ({len(bookings)} шт.)</b>\n\nВыберите заявку ниже:",
        parse_mode="HTML",
        reply_markup=back_to_admin_kb(),
    )

    # Отправляем каждую заявку отдельным сообщением с кнопками
    for b in bookings:
        text = (
            f"🔖 <b>Заявка #{b['id']}</b>\n"
            f"👤 {b['full_name']} (@{b.get('username', '—')})\n"
            f"🆔 <code>{b['telegram_id']}</code>\n"
            f"🎮 Зона: <b>{b['zone']}</b>\n"
            f"📅 {b['booking_date']} {b['booking_time']} ({b['duration']} ч.)"
        )
        await callback.bot.send_message(
            callback.from_user.id,
            text,
            parse_mode="HTML",
            reply_markup=booking_actions_kb(b["id"]),
        )

    await callback.answer()


# ──────────────────────────────────────────────
# ПОДТВЕРЖДЕНИЕ ЗАЯВКИ
# ──────────────────────────────────────────────

@router.callback_query(F.data.startswith("adm_book:confirm:"))
@admin_only
async def admin_confirm_booking(callback: CallbackQuery):
    booking_id = int(callback.data.split(":")[2])
    booking = await get_booking_by_id(booking_id)

    if not booking:
        await callback.answer("❌ Заявка не найдена.", show_alert=True)
        return

    await update_booking_status(booking_id, "confirmed", "Ваша бронь подтверждена!")
    booking["status"] = "confirmed"
    booking["admin_comment"] = "Ваша бронь подтверждена!"

    await callback.message.edit_text(
        f"✅ Заявка <b>#{booking_id}</b> подтверждена.",
        parse_mode="HTML",
        reply_markup=back_to_bookings_kb(),
    )

    # Уведомляем пользователя
    await notify_booking_status_changed(callback.bot, booking, booking["telegram_id"])
    await callback.answer("Подтверждено!")
    logger.info("Администратор %d подтвердил бронь #%d", callback.from_user.id, booking_id)


# ──────────────────────────────────────────────
# ОТКЛОНЕНИЕ ЗАЯВКИ
# ──────────────────────────────────────────────

@router.callback_query(F.data.startswith("adm_book:reject:"))
@admin_only
async def admin_reject_booking(callback: CallbackQuery):
    booking_id = int(callback.data.split(":")[2])
    booking = await get_booking_by_id(booking_id)

    if not booking:
        await callback.answer("❌ Заявка не найдена.", show_alert=True)
        return

    comment = "К сожалению, ваша заявка была отклонена. Пожалуйста, выберите другое время."
    await update_booking_status(booking_id, "rejected", comment)
    booking["status"] = "rejected"
    booking["admin_comment"] = comment

    await callback.message.edit_text(
        f"❌ Заявка <b>#{booking_id}</b> отклонена.",
        parse_mode="HTML",
        reply_markup=back_to_bookings_kb(),
    )

    await notify_booking_status_changed(callback.bot, booking, booking["telegram_id"])
    await callback.answer("Отклонено!")
    logger.info("Администратор %d отклонил бронь #%d", callback.from_user.id, booking_id)


# ──────────────────────────────────────────────
# ПРЕДЛОЖИТЬ ДРУГОЕ ВРЕМЯ
# ──────────────────────────────────────────────

@router.callback_query(F.data.startswith("adm_book:propose:"))
@admin_only
async def admin_propose_time_start(callback: CallbackQuery, state: FSMContext):
    booking_id = int(callback.data.split(":")[2])
    await state.set_state(AdminBookingFSM.propose_time_message)
    await state.update_data(booking_id=booking_id)

    await callback.message.edit_text(
        f"⏰ Введите сообщение для пользователя по заявке <b>#{booking_id}</b>:\n"
        "(Например: «Свободно с 15:00, устроит?»)",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminBookingFSM.propose_time_message, F.text)
@admin_only
async def admin_propose_time_send(message: Message, state: FSMContext):
    data = await state.get_data()
    booking_id = data["booking_id"]
    await state.clear()

    booking = await get_booking_by_id(booking_id)
    if not booking:
        await message.answer("❌ Заявка не найдена.")
        return

    # Статус остаётся pending, но добавляем комментарий
    await update_booking_status(booking_id, "pending", message.text)
    booking["status"] = "pending"
    booking["admin_comment"] = message.text

    # Уведомляем пользователя
    await notify_booking_status_changed(message.bot, booking, booking["telegram_id"])

    await message.answer(
        f"✅ Сообщение отправлено пользователю по заявке #{booking_id}.",
        reply_markup=admin_menu_kb(),
    )
    logger.info(
        "Администратор %d предложил другое время по брони #%d",
        message.from_user.id,
        booking_id,
    )

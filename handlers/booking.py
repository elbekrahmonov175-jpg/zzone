"""
Хендлер бронирования — FSM с шагами:
  выбор зоны → дата → время → длительность → подтверждение.
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import (
    create_booking,
    get_booking_by_id,
    get_user_bookings,
    cancel_booking,
    get_user_by_telegram_id,
)
from keyboards.user_kb import (
    zones_kb,
    dates_kb,
    times_kb,
    durations_kb,
    confirm_booking_kb,
    active_bookings_kb,
    main_menu_kb,
)
from utils.notifications import notify_new_booking, notify_booking_cancelled_to_admins

logger = logging.getLogger(__name__)
router = Router()


# ──────────────────────────────────────────────
# FSM СОСТОЯНИЯ
# ──────────────────────────────────────────────

class BookingFSM(StatesGroup):
    zone     = State()
    date     = State()
    time     = State()
    duration = State()
    confirm  = State()


# ──────────────────────────────────────────────
# НАЧАЛО БРОНИРОВАНИЯ
# ──────────────────────────────────────────────

@router.message(F.text == "🎮 Забронировать место")
async def start_booking(message: Message, state: FSMContext, is_blacklisted: bool):
    """Запускает процесс бронирования."""
    if is_blacklisted:
        await message.answer(
            "🚫 К сожалению, вам запрещено создавать бронирования.\n"
            "Свяжитесь с администратором для уточнения причин."
        )
        return

    await state.set_state(BookingFSM.zone)
    await message.answer(
        "🎮 <b>Шаг 1 из 4 — Выберите зону</b>\n\n"
        "🖥 <b>Standard</b> — обычные ПК\n"
        "👑 <b>VIP</b> — топовые ПК в отдельных кабинках\n"
        "🎮 <b>PS5</b> — PlayStation 5",
        parse_mode="HTML",
        reply_markup=zones_kb(),
    )


# ──────────────────────────────────────────────
# ВЫБОР ЗОНЫ
# ──────────────────────────────────────────────

@router.callback_query(BookingFSM.zone, F.data.startswith("zone:"))
async def choose_zone(callback: CallbackQuery, state: FSMContext):
    zone = callback.data.split(":")[1]
    await state.update_data(zone=zone)
    await state.set_state(BookingFSM.date)

    await callback.message.edit_text(
        f"✅ Зона: <b>{zone}</b>\n\n"
        "📅 <b>Шаг 2 из 4 — Выберите дату</b>",
        parse_mode="HTML",
        reply_markup=dates_kb(),
    )
    await callback.answer()


@router.callback_query(BookingFSM.zone, F.data == "booking:cancel")
async def cancel_booking_fsm_zone(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Бронирование отменено.")
    await callback.answer()


# ──────────────────────────────────────────────
# ВЫБОР ДАТЫ
# ──────────────────────────────────────────────

@router.callback_query(BookingFSM.date, F.data.startswith("date:"))
async def choose_date(callback: CallbackQuery, state: FSMContext):
    date_str = callback.data.split(":")[1]
    await state.update_data(date=date_str)
    await state.set_state(BookingFSM.time)

    await callback.message.edit_text(
        f"✅ Дата: <b>{date_str}</b>\n\n"
        "⏰ <b>Шаг 3 из 4 — Выберите время начала</b>",
        parse_mode="HTML",
        reply_markup=times_kb(),
    )
    await callback.answer()


@router.callback_query(BookingFSM.date, F.data == "booking:back_to_zone")
async def back_to_zone(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BookingFSM.zone)
    await callback.message.edit_text(
        "🎮 <b>Шаг 1 из 4 — Выберите зону</b>",
        parse_mode="HTML",
        reply_markup=zones_kb(),
    )
    await callback.answer()


# ──────────────────────────────────────────────
# ВЫБОР ВРЕМЕНИ
# ──────────────────────────────────────────────

@router.callback_query(BookingFSM.time, F.data.startswith("time:"))
async def choose_time(callback: CallbackQuery, state: FSMContext):
    time_str = callback.data.split(":")[1]
    await state.update_data(time=time_str)
    await state.set_state(BookingFSM.duration)

    await callback.message.edit_text(
        f"✅ Время: <b>{time_str}</b>\n\n"
        "⏱ <b>Шаг 4 из 4 — Выберите длительность</b>",
        parse_mode="HTML",
        reply_markup=durations_kb(),
    )
    await callback.answer()


@router.callback_query(BookingFSM.time, F.data == "booking:back_to_date")
async def back_to_date(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BookingFSM.date)
    await callback.message.edit_text(
        "📅 <b>Шаг 2 из 4 — Выберите дату</b>",
        parse_mode="HTML",
        reply_markup=dates_kb(),
    )
    await callback.answer()


# ──────────────────────────────────────────────
# ВЫБОР ДЛИТЕЛЬНОСТИ
# ──────────────────────────────────────────────

@router.callback_query(BookingFSM.duration, F.data.startswith("duration:"))
async def choose_duration(callback: CallbackQuery, state: FSMContext):
    duration = int(callback.data.split(":")[1])
    await state.update_data(duration=duration)
    await state.set_state(BookingFSM.confirm)

    data = await state.get_data()
    await callback.message.edit_text(
        "📋 <b>Подтверждение заявки</b>\n\n"
        f"🎮 Зона: <b>{data['zone']}</b>\n"
        f"📅 Дата: <b>{data['date']}</b>\n"
        f"⏰ Время: <b>{data['time']}</b>\n"
        f"⏱ Длительность: <b>{data['duration']} ч.</b>\n\n"
        "Всё верно? Нажмите <b>Подтвердить</b> для отправки заявки администратору.",
        parse_mode="HTML",
        reply_markup=confirm_booking_kb(),
    )
    await callback.answer()


@router.callback_query(BookingFSM.duration, F.data == "booking:back_to_time")
async def back_to_time(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BookingFSM.time)
    await callback.message.edit_text(
        "⏰ <b>Шаг 3 из 4 — Выберите время начала</b>",
        parse_mode="HTML",
        reply_markup=times_kb(),
    )
    await callback.answer()


# ──────────────────────────────────────────────
# ПОДТВЕРЖДЕНИЕ
# ──────────────────────────────────────────────

@router.callback_query(BookingFSM.confirm, F.data == "booking:confirm")
async def confirm_booking(callback: CallbackQuery, state: FSMContext, db_user: dict):
    data = await state.get_data()
    await state.clear()

    # Создаём бронь в базе
    booking_id = await create_booking(
        user_id=db_user["id"],
        zone=data["zone"],
        booking_date=data["date"],
        booking_time=data["time"],
        duration=data["duration"],
    )
    booking = await get_booking_by_id(booking_id)

    await callback.message.edit_text(
        "✅ <b>Заявка отправлена!</b>\n\n"
        f"🔖 Номер заявки: <b>#{booking_id}</b>\n\n"
        "Ваша заявка отправлена администратору и ожидает подтверждения.\n"
        "Мы уведомим вас, как только статус изменится.",
        parse_mode="HTML",
        reply_markup=None,
    )

    # Уведомляем администраторов
    await notify_new_booking(callback.bot, booking, db_user)
    await callback.answer("Заявка создана!")
    logger.info("Создана бронь #%d пользователем %d", booking_id, callback.from_user.id)


@router.callback_query(BookingFSM.confirm, F.data == "booking:cancel")
async def cancel_confirm(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Бронирование отменено.")
    await callback.answer()


# ──────────────────────────────────────────────
# МОИ БРОНИРОВАНИЯ
# ──────────────────────────────────────────────

@router.message(F.text == "📋 Мои бронирования")
async def my_bookings(message: Message, db_user: dict):
    """Показывает все брони пользователя."""
    from database import STATUS_LABELS
    bookings = await get_user_bookings(db_user["id"])

    if not bookings:
        await message.answer("У вас ещё нет бронирований.", reply_markup=main_menu_kb())
        return

    text = "📋 <b>Ваши бронирования:</b>\n\n"
    for b in bookings:
        status = STATUS_LABELS.get(b["status"], b["status"])
        text += (
            f"🔖 <b>#{b['id']}</b>\n"
            f"🎮 Зона: {b['zone']}\n"
            f"📅 {b['booking_date']} {b['booking_time']} ({b['duration']} ч.)\n"
            f"Статус: {status}\n"
        )
        if b.get("admin_comment"):
            text += f"💬 {b['admin_comment']}\n"
        text += "\n"

    await message.answer(text, parse_mode="HTML", reply_markup=main_menu_kb())


# ──────────────────────────────────────────────
# ОТМЕНА БРОНИ
# ──────────────────────────────────────────────

@router.message(F.text == "❌ Отменить бронь")
async def show_cancellable_bookings(message: Message, db_user: dict):
    """Показывает активные брони для отмены."""
    bookings = await get_user_bookings(db_user["id"], active_only=True)

    if not bookings:
        await message.answer(
            "У вас нет активных бронирований для отмены.",
            reply_markup=main_menu_kb(),
        )
        return

    await message.answer(
        "🚫 <b>Выберите бронирование для отмены:</b>",
        parse_mode="HTML",
        reply_markup=active_bookings_kb(bookings),
    )


@router.callback_query(F.data.startswith("cancel_booking:"))
async def process_cancel_booking(callback: CallbackQuery, db_user: dict):
    """Обрабатывает отмену конкретной брони."""
    booking_id = int(callback.data.split(":")[1])
    booking = await get_booking_by_id(booking_id)

    success = await cancel_booking(booking_id, db_user["id"])
    if success:
        await callback.message.edit_text(
            f"✅ Бронирование <b>#{booking_id}</b> успешно отменено.",
            parse_mode="HTML",
        )
        # Уведомляем администраторов
        if booking:
            await notify_booking_cancelled_to_admins(callback.bot, booking, db_user)
        logger.info("Бронь #%d отменена пользователем %d", booking_id, callback.from_user.id)
    else:
        await callback.answer("❌ Не удалось отменить бронирование.", show_alert=True)

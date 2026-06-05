"""
Клавиатуры для пользовательской части бота.
Используются InlineKeyboardMarkup и ReplyKeyboardMarkup.
"""

from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


# ──────────────────────────────────────────────
# ГЛАВНОЕ МЕНЮ
# ──────────────────────────────────────────────

def main_menu_kb() -> ReplyKeyboardMarkup:
    """Главное меню пользователя."""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="🎮 Забронировать место"),
        KeyboardButton(text="💰 Прайс-лист"),
    )
    builder.row(
        KeyboardButton(text="🎁 Акции"),
        KeyboardButton(text="📍 Локация"),
    )
    builder.row(
        KeyboardButton(text="💬 Связаться с администратором"),
    )
    builder.row(
        KeyboardButton(text="❌ Отменить бронь"),
        KeyboardButton(text="📋 Мои бронирования"),
    )
    return builder.as_markup(resize_keyboard=True)


# ──────────────────────────────────────────────
# БРОНИРОВАНИЕ: ВЫБОР ЗОНЫ
# ──────────────────────────────────────────────

def zones_kb() -> InlineKeyboardMarkup:
    """Выбор игровой зоны."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🖥 Standard", callback_data="zone:Standard"))
    builder.row(InlineKeyboardButton(text="👑 VIP",      callback_data="zone:VIP"))
    builder.row(InlineKeyboardButton(text="🎮 PS5",      callback_data="zone:PS5"))
    builder.row(InlineKeyboardButton(text="🔙 Отмена",   callback_data="booking:cancel"))
    return builder.as_markup()


# ──────────────────────────────────────────────
# БРОНИРОВАНИЕ: ВЫБОР ДАТЫ
# ──────────────────────────────────────────────

def dates_kb() -> InlineKeyboardMarkup:
    """Предлагает выбор ближайших 7 дней."""
    from datetime import date, timedelta
    builder = InlineKeyboardBuilder()
    today = date.today()
    days_ru = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    for i in range(7):
        d = today + timedelta(days=i)
        label = ("Сегодня" if i == 0 else "Завтра" if i == 1 else
                 f"{days_ru[d.weekday()]} {d.strftime('%d.%m')}")
        builder.row(InlineKeyboardButton(
            text=label,
            callback_data=f"date:{d.isoformat()}"
        ))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="booking:back_to_zone"))
    return builder.as_markup()


# ──────────────────────────────────────────────
# БРОНИРОВАНИЕ: ВЫБОР ВРЕМЕНИ
# ──────────────────────────────────────────────

def times_kb() -> InlineKeyboardMarkup:
    """Выбор времени начала (с 10:00 до 23:00 каждый час)."""
    builder = InlineKeyboardBuilder()
    hours = [f"{h:02d}:00" for h in range(10, 24)]
    # Кнопки по 3 в ряд
    for i in range(0, len(hours), 3):
        row = hours[i:i+3]
        builder.row(*[
            InlineKeyboardButton(text=t, callback_data=f"time:{t}")
            for t in row
        ])
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="booking:back_to_date"))
    return builder.as_markup()


# ──────────────────────────────────────────────
# БРОНИРОВАНИЕ: ВЫБОР ДЛИТЕЛЬНОСТИ
# ──────────────────────────────────────────────

def durations_kb() -> InlineKeyboardMarkup:
    """Выбор длительности сеанса."""
    builder = InlineKeyboardBuilder()
    durations = [1, 2, 3, 4, 5, 6, 8, 10, 12]
    for i in range(0, len(durations), 3):
        row = durations[i:i+3]
        builder.row(*[
            InlineKeyboardButton(
                text=f"{d} ч",
                callback_data=f"duration:{d}"
            )
            for d in row
        ])
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="booking:back_to_time"))
    return builder.as_markup()


# ──────────────────────────────────────────────
# БРОНИРОВАНИЕ: ПОДТВЕРЖДЕНИЕ
# ──────────────────────────────────────────────

def confirm_booking_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data="booking:confirm"),
        InlineKeyboardButton(text="❌ Отмена",      callback_data="booking:cancel"),
    )
    return builder.as_markup()


# ──────────────────────────────────────────────
# МОИ БРОНИ: ОТМЕНА
# ──────────────────────────────────────────────

def active_bookings_kb(bookings: list) -> InlineKeyboardMarkup:
    """Inline-кнопки для отмены активных броней."""
    builder = InlineKeyboardBuilder()
    for b in bookings:
        label = f"#{b['id']} {b['booking_date']} {b['booking_time']} — {b['zone']}"
        builder.row(InlineKeyboardButton(
            text=f"❌ Отменить {label}",
            callback_data=f"cancel_booking:{b['id']}"
        ))
    return builder.as_markup()


def remove_kb() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()

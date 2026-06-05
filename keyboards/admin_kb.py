"""
Клавиатуры для административной части бота.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


# ──────────────────────────────────────────────
# ГЛАВНОЕ МЕНЮ АДМИНА
# ──────────────────────────────────────────────

def admin_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📋 Новые заявки",         callback_data="admin:bookings"))
    builder.row(InlineKeyboardButton(text="📊 Статистика",           callback_data="admin:stats"))
    builder.row(
        InlineKeyboardButton(text="💰 Цены",   callback_data="admin:prices"),
        InlineKeyboardButton(text="🎁 Акции",  callback_data="admin:promos"),
    )
    builder.row(InlineKeyboardButton(text="📍 Локация",              callback_data="admin:location"))
    builder.row(InlineKeyboardButton(text="📢 Рассылка",             callback_data="admin:broadcast"))
    builder.row(InlineKeyboardButton(text="🚫 Чёрный список",        callback_data="admin:blacklist"))
    return builder.as_markup()


# ──────────────────────────────────────────────
# УПРАВЛЕНИЕ БРОНИРОВАНИЕМ
# ──────────────────────────────────────────────

def booking_actions_kb(booking_id: int) -> InlineKeyboardMarkup:
    """Кнопки действий по конкретной заявке."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Подтвердить",          callback_data=f"adm_book:confirm:{booking_id}"),
        InlineKeyboardButton(text="❌ Отклонить",             callback_data=f"adm_book:reject:{booking_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="⏰ Предложить другое время", callback_data=f"adm_book:propose:{booking_id}"),
    )
    return builder.as_markup()


def back_to_bookings_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔙 К заявкам", callback_data="admin:bookings"))
    return builder.as_markup()


# ──────────────────────────────────────────────
# УПРАВЛЕНИЕ ЦЕНАМИ
# ──────────────────────────────────────────────

def prices_edit_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for zone in ("Standard", "VIP", "PS5"):
        builder.row(InlineKeyboardButton(
            text=f"✏️ {zone}",
            callback_data=f"edit_price:{zone}"
        ))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin:menu"))
    return builder.as_markup()


# ──────────────────────────────────────────────
# УПРАВЛЕНИЕ АКЦИЯМИ
# ──────────────────────────────────────────────

def promos_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="➕ Создать акцию",  callback_data="promo:create"))
    builder.row(InlineKeyboardButton(text="📋 Список акций",   callback_data="promo:list"))
    builder.row(InlineKeyboardButton(text="🔙 Назад",          callback_data="admin:menu"))
    return builder.as_markup()


def promo_actions_kb(promo_id: int, is_active: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    toggle_label = "🔴 Деактивировать" if is_active else "🟢 Активировать"
    builder.row(
        InlineKeyboardButton(text="✏️ Изменить",   callback_data=f"promo:edit:{promo_id}"),
        InlineKeyboardButton(text=toggle_label,    callback_data=f"promo:toggle:{promo_id}"),
    )
    builder.row(InlineKeyboardButton(text="🗑 Удалить",  callback_data=f"promo:delete:{promo_id}"))
    builder.row(InlineKeyboardButton(text="🔙 Назад",    callback_data="promo:list"))
    return builder.as_markup()


# ──────────────────────────────────────────────
# РАССЫЛКА
# ──────────────────────────────────────────────

def broadcast_type_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📝 Текст",  callback_data="broadcast:text"),
        InlineKeyboardButton(text="🖼 Фото",   callback_data="broadcast:photo"),
        InlineKeyboardButton(text="🎥 Видео",  callback_data="broadcast:video"),
    )
    builder.row(InlineKeyboardButton(text="🔙 Отмена", callback_data="admin:menu"))
    return builder.as_markup()


def broadcast_confirm_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📢 Отправить всем", callback_data="broadcast:send"),
        InlineKeyboardButton(text="❌ Отмена",          callback_data="admin:menu"),
    )
    return builder.as_markup()


# ──────────────────────────────────────────────
# ЧЁРНЫЙ СПИСОК
# ──────────────────────────────────────────────

def blacklist_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="➕ Добавить",    callback_data="bl:add"))
    builder.row(InlineKeyboardButton(text="➖ Удалить",     callback_data="bl:remove"))
    builder.row(InlineKeyboardButton(text="📋 Просмотреть", callback_data="bl:view"))
    builder.row(InlineKeyboardButton(text="🔙 Назад",       callback_data="admin:menu"))
    return builder.as_markup()


# ──────────────────────────────────────────────
# ОБЩИЕ
# ──────────────────────────────────────────────

def back_to_admin_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔙 В меню", callback_data="admin:menu"))
    return builder.as_markup()

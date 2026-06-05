"""
Административные хендлеры:
статистика, редактирование цен, акций, локации.
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config.settings import settings
from database import (
    get_statistics,
    get_prices,
    update_price,
    get_all_promotions,
    get_promotion_by_id,
    create_promotion,
    update_promotion,
    delete_promotion,
    get_location,
    update_location,
)
from keyboards.admin_kb import (
    admin_menu_kb,
    prices_edit_kb,
    promos_menu_kb,
    promo_actions_kb,
    back_to_admin_kb,
)

logger = logging.getLogger(__name__)
router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in settings.ADMIN_IDS


# ──────────────────────────────────────────────
# СТАТИСТИКА
# ──────────────────────────────────────────────

@router.callback_query(F.data == "admin:stats")
async def admin_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    s = await get_statistics()

    zone_lines = ""
    for z in s.get("popular_zones", []):
        zone_lines += f"  • {z['zone']}: {z['cnt']} броней\n"

    text = (
        "📊 <b>Статистика</b>\n\n"
        f"👥 Всего пользователей: <b>{s['total_users']}</b>\n"
        f"🆕 Новых сегодня: <b>{s['new_users_today']}</b>\n"
        f"📆 За этот месяц: <b>{s['users_this_month']}</b>\n\n"
        f"📋 Всего броней: <b>{s['total_bookings']}</b>\n"
        f"⏳ Ожидают: <b>{s['bookings_pending']}</b>\n"
        f"✅ Подтверждены: <b>{s['bookings_confirmed']}</b>\n"
        f"❌ Отклонены: <b>{s['bookings_rejected']}</b>\n"
        f"🚫 Отменены: <b>{s['bookings_cancelled']}</b>\n"
        f"🔥 Активные: <b>{s['active_bookings']}</b>\n\n"
        f"🏆 <b>Популярные зоны:</b>\n{zone_lines or '  Нет данных'}"
    )

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_to_admin_kb())
    await callback.answer()


# ──────────────────────────────────────────────
# ЦЕНЫ
# ──────────────────────────────────────────────

class PriceFSM(StatesGroup):
    waiting_price = State()


@router.callback_query(F.data == "admin:prices")
async def admin_prices(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    prices = await get_prices()
    text = "💰 <b>Текущие цены</b>\n\n"
    for p in prices:
        text += f"• {p['zone']}: <b>{p['price_hour']:,}</b> сум/час\n"
    text += "\nВыберите зону для редактирования:"

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=prices_edit_kb())
    await callback.answer()


@router.callback_query(F.data.startswith("edit_price:"))
async def edit_price_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    zone = callback.data.split(":")[1]
    await state.set_state(PriceFSM.waiting_price)
    await state.update_data(zone=zone)

    await callback.message.edit_text(
        f"✏️ Введите новую цену за час для зоны <b>{zone}</b> (в сумах):",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(PriceFSM.waiting_price, F.text)
async def edit_price_save(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return

    data = await state.get_data()
    zone = data["zone"]

    if not message.text.isdigit():
        await message.answer("❌ Введите целое число (только цифры).")
        return

    new_price = int(message.text)
    await update_price(zone, new_price)
    await state.clear()

    await message.answer(
        f"✅ Цена для <b>{zone}</b> обновлена: <b>{new_price:,}</b> сум/час",
        parse_mode="HTML",
        reply_markup=admin_menu_kb(),
    )
    logger.info(
        "Администратор %d изменил цену %s → %d",
        message.from_user.id, zone, new_price,
    )


# ──────────────────────────────────────────────
# АКЦИИ
# ──────────────────────────────────────────────

class PromoFSM(StatesGroup):
    create_title       = State()
    create_description = State()
    edit_title         = State()
    edit_description   = State()


@router.callback_query(F.data == "admin:promos")
async def admin_promos(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    await callback.message.edit_text(
        "🎁 <b>Управление акциями</b>",
        parse_mode="HTML",
        reply_markup=promos_menu_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "promo:list")
async def promo_list(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    promos = await get_all_promotions()
    if not promos:
        await callback.message.edit_text(
            "Акций нет. Создайте первую!",
            reply_markup=promos_menu_kb(),
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        f"🎁 <b>Все акции ({len(promos)})</b>",
        parse_mode="HTML",
        reply_markup=promos_menu_kb(),
    )
    for p in promos:
        status = "🟢 Активна" if p["is_active"] else "🔴 Неактивна"
        text = f"<b>{p['title']}</b>\n{p['description']}\n{status}"
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        from aiogram.types import InlineKeyboardButton
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(
            text=f"⚙️ Управление #{p['id']}",
            callback_data=f"promo:manage:{p['id']}"
        ))
        await callback.bot.send_message(
            callback.from_user.id, text,
            parse_mode="HTML",
            reply_markup=builder.as_markup(),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("promo:manage:"))
async def promo_manage(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    promo_id = int(callback.data.split(":")[2])
    promo = await get_promotion_by_id(promo_id)
    if not promo:
        await callback.answer("Акция не найдена.", show_alert=True)
        return

    status = "🟢 Активна" if promo["is_active"] else "🔴 Неактивна"
    await callback.message.edit_text(
        f"<b>{promo['title']}</b>\n{promo['description']}\n{status}",
        parse_mode="HTML",
        reply_markup=promo_actions_kb(promo_id, promo["is_active"]),
    )
    await callback.answer()


@router.callback_query(F.data == "promo:create")
async def promo_create_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(PromoFSM.create_title)
    await callback.message.edit_text("✏️ Введите название акции:")
    await callback.answer()


@router.message(PromoFSM.create_title, F.text)
async def promo_create_title(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    await state.update_data(title=message.text)
    await state.set_state(PromoFSM.create_description)
    await message.answer("✏️ Введите описание акции:")


@router.message(PromoFSM.create_description, F.text)
async def promo_create_desc(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return

    data = await state.get_data()
    await state.clear()

    promo_id = await create_promotion(data["title"], message.text)
    await message.answer(
        f"✅ Акция <b>#{promo_id}</b> создана!",
        parse_mode="HTML",
        reply_markup=admin_menu_kb(),
    )


@router.callback_query(F.data.startswith("promo:toggle:"))
async def promo_toggle(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    promo_id = int(callback.data.split(":")[2])
    promo = await get_promotion_by_id(promo_id)
    if not promo:
        await callback.answer("Акция не найдена.", show_alert=True)
        return

    new_active = 0 if promo["is_active"] else 1
    await update_promotion(promo_id, promo["title"], promo["description"], new_active)

    status = "активирована 🟢" if new_active else "деактивирована 🔴"
    await callback.answer(f"Акция {status}!", show_alert=True)

    # Обновляем сообщение
    promo["is_active"] = new_active
    await callback.message.edit_reply_markup(
        reply_markup=promo_actions_kb(promo_id, new_active)
    )


@router.callback_query(F.data.startswith("promo:delete:"))
async def promo_delete(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    promo_id = int(callback.data.split(":")[2])
    await delete_promotion(promo_id)
    await callback.message.edit_text(
        f"🗑 Акция #{promo_id} удалена.",
        reply_markup=promos_menu_kb(),
    )
    await callback.answer()


# ──────────────────────────────────────────────
# ЛОКАЦИЯ
# ──────────────────────────────────────────────

class LocationFSM(StatesGroup):
    address   = State()
    phone     = State()
    telegram  = State()
    coords    = State()  # "lat,lon"


@router.callback_query(F.data == "admin:location")
async def admin_location(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    loc = await get_location()
    text = (
        "📍 <b>Текущая локация</b>\n\n"
        f"🏠 Адрес: {loc['address']}\n"
        f"📞 Телефон: {loc['phone']}\n"
        f"💬 Telegram: {loc['telegram']}\n"
        f"🗺 Координаты: {loc['latitude']}, {loc['longitude']}\n\n"
        "Нажмите кнопку, чтобы изменить данные:"
    )
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✏️ Изменить", callback_data="location:edit"))
    builder.row(InlineKeyboardButton(text="🔙 Назад",    callback_data="admin:menu"))

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "location:edit")
async def location_edit_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(LocationFSM.address)
    await callback.message.edit_text("🏠 Введите новый адрес клуба:")
    await callback.answer()


@router.message(LocationFSM.address, F.text)
async def location_set_address(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    await state.update_data(address=message.text)
    await state.set_state(LocationFSM.phone)
    await message.answer("📞 Введите номер телефона:")


@router.message(LocationFSM.phone, F.text)
async def location_set_phone(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    await state.update_data(phone=message.text)
    await state.set_state(LocationFSM.telegram)
    await message.answer("💬 Введите Telegram-контакт (например @club):")


@router.message(LocationFSM.telegram, F.text)
async def location_set_telegram(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    await state.update_data(telegram=message.text)
    await state.set_state(LocationFSM.coords)
    await message.answer(
        "🗺 Введите координаты в формате: <b>широта,долгота</b>\n"
        "Пример: 41.2995,69.2401",
        parse_mode="HTML",
    )


@router.message(LocationFSM.coords, F.text)
async def location_set_coords(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return

    try:
        lat_str, lon_str = message.text.replace(" ", "").split(",")
        lat, lon = float(lat_str), float(lon_str)
    except (ValueError, AttributeError):
        await message.answer(
            "❌ Неверный формат. Введите: <b>широта,долгота</b>\nПример: 41.2995,69.2401",
            parse_mode="HTML",
        )
        return

    data = await state.get_data()
    await state.clear()

    await update_location(data["address"], data["phone"], data["telegram"], lat, lon)

    await message.answer(
        "✅ Локация обновлена!",
        reply_markup=admin_menu_kb(),
    )
    logger.info("Администратор %d обновил локацию", message.from_user.id)

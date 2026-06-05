"""
Административные хендлеры: рассылка и чёрный список.
"""

import logging
import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config.settings import settings
from database import (
    get_all_users,
    add_to_blacklist,
    remove_from_blacklist,
    get_blacklist,
)
from keyboards.admin_kb import (
    admin_menu_kb,
    broadcast_type_kb,
    broadcast_confirm_kb,
    blacklist_menu_kb,
    back_to_admin_kb,
)

logger = logging.getLogger(__name__)
router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in settings.ADMIN_IDS


# ──────────────────────────────────────────────
# РАССЫЛКА
# ──────────────────────────────────────────────

class BroadcastFSM(StatesGroup):
    choosing_type = State()
    waiting_content = State()
    confirming = State()


@router.callback_query(F.data == "admin:broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(BroadcastFSM.choosing_type)
    await callback.message.edit_text(
        "📢 <b>Рассылка</b>\n\nВыберите тип сообщения:",
        parse_mode="HTML",
        reply_markup=broadcast_type_kb(),
    )
    await callback.answer()


@router.callback_query(BroadcastFSM.choosing_type, F.data.startswith("broadcast:"))
async def broadcast_type_chosen(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    msg_type = callback.data.split(":")[1]
    if msg_type not in ("text", "photo", "video"):
        return

    await state.update_data(msg_type=msg_type)
    await state.set_state(BroadcastFSM.waiting_content)

    prompts = {
        "text":  "✏️ Отправьте текст сообщения для рассылки:",
        "photo": "🖼 Отправьте фото с подписью (или без) для рассылки:",
        "video": "🎥 Отправьте видео с подписью (или без) для рассылки:",
    }
    await callback.message.edit_text(prompts[msg_type])
    await callback.answer()


@router.message(BroadcastFSM.waiting_content)
async def broadcast_content_received(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return

    data = await state.get_data()
    msg_type = data["msg_type"]

    # Сохраняем нужные поля в зависимости от типа
    update = {}
    if msg_type == "text" and message.text:
        update["text"] = message.text
        preview = message.text[:100]
    elif msg_type == "photo" and message.photo:
        update["file_id"] = message.photo[-1].file_id
        update["caption"] = message.caption or ""
        preview = f"[Фото] {message.caption or ''}"
    elif msg_type == "video" and message.video:
        update["file_id"] = message.video.file_id
        update["caption"] = message.caption or ""
        preview = f"[Видео] {message.caption or ''}"
    else:
        await message.answer("❌ Неподходящий тип сообщения. Попробуйте ещё раз.")
        return

    await state.update_data(**update)
    await state.set_state(BroadcastFSM.confirming)

    users = await get_all_users()
    await message.answer(
        f"📢 <b>Предпросмотр рассылки</b>\n\n"
        f"📝 {preview}\n\n"
        f"👥 Получателей: <b>{len(users)}</b>\n\n"
        "Отправить?",
        parse_mode="HTML",
        reply_markup=broadcast_confirm_kb(),
    )


@router.callback_query(BroadcastFSM.confirming, F.data == "broadcast:send")
async def broadcast_send(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    data = await state.get_data()
    await state.clear()

    users = await get_all_users()
    msg_type = data["msg_type"]

    sent = 0
    errors = 0

    await callback.message.edit_text(
        f"📤 Отправляем рассылку {len(users)} пользователям...",
        reply_markup=None,
    )

    for user in users:
        tg_id = user["telegram_id"]
        try:
            if msg_type == "text":
                await callback.bot.send_message(tg_id, data["text"])
            elif msg_type == "photo":
                await callback.bot.send_photo(
                    tg_id, data["file_id"],
                    caption=data.get("caption", ""),
                )
            elif msg_type == "video":
                await callback.bot.send_video(
                    tg_id, data["file_id"],
                    caption=data.get("caption", ""),
                )
            sent += 1
        except Exception as e:
            logger.warning("Рассылка: ошибка для %d: %s", tg_id, e)
            errors += 1

        # Небольшая пауза, чтобы не попасть под flood-limit Telegram
        await asyncio.sleep(0.05)

    await callback.message.edit_text(
        f"📢 <b>Рассылка завершена!</b>\n\n"
        f"✅ Успешно: <b>{sent}</b>\n"
        f"❌ Ошибок: <b>{errors}</b>",
        parse_mode="HTML",
        reply_markup=back_to_admin_kb(),
    )
    logger.info(
        "Рассылка от admin %d: %d успешно, %d ошибок",
        callback.from_user.id, sent, errors,
    )


# ──────────────────────────────────────────────
# ЧЁРНЫЙ СПИСОК
# ──────────────────────────────────────────────

class BlacklistFSM(StatesGroup):
    add_id    = State()
    add_reason = State()
    remove_id = State()


@router.callback_query(F.data == "admin:blacklist")
async def admin_blacklist(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    await callback.message.edit_text(
        "🚫 <b>Чёрный список</b>",
        parse_mode="HTML",
        reply_markup=blacklist_menu_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "bl:view")
async def bl_view(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    bl = await get_blacklist()
    if not bl:
        await callback.message.edit_text(
            "📋 Чёрный список пуст.",
            reply_markup=blacklist_menu_kb(),
        )
        await callback.answer()
        return

    text = "🚫 <b>Чёрный список:</b>\n\n"
    for entry in bl:
        name = entry.get("full_name") or "Неизвестно"
        username = entry.get("username") or "—"
        reason = entry.get("reason") or "Причина не указана"
        text += (
            f"• <code>{entry['telegram_id']}</code> — {name} (@{username})\n"
            f"  Причина: {reason}\n\n"
        )

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=blacklist_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "bl:add")
async def bl_add_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(BlacklistFSM.add_id)
    await callback.message.edit_text(
        "🚫 Введите Telegram ID пользователя для добавления в чёрный список:"
    )
    await callback.answer()


@router.message(BlacklistFSM.add_id, F.text)
async def bl_add_get_id(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return

    if not message.text.lstrip("-").isdigit():
        await message.answer("❌ Введите числовой Telegram ID.")
        return

    await state.update_data(bl_user_id=int(message.text))
    await state.set_state(BlacklistFSM.add_reason)
    await message.answer("💬 Введите причину (или напишите «-» чтобы пропустить):")


@router.message(BlacklistFSM.add_reason, F.text)
async def bl_add_save(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return

    data = await state.get_data()
    await state.clear()

    reason = message.text if message.text != "-" else None
    await add_to_blacklist(data["bl_user_id"], reason)

    await message.answer(
        f"✅ Пользователь <code>{data['bl_user_id']}</code> добавлен в чёрный список.",
        parse_mode="HTML",
        reply_markup=admin_menu_kb(),
    )
    logger.info(
        "Admin %d добавил %d в blacklist (причина: %s)",
        message.from_user.id, data["bl_user_id"], reason,
    )


@router.callback_query(F.data == "bl:remove")
async def bl_remove_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(BlacklistFSM.remove_id)
    await callback.message.edit_text(
        "➖ Введите Telegram ID пользователя для удаления из чёрного списка:"
    )
    await callback.answer()


@router.message(BlacklistFSM.remove_id, F.text)
async def bl_remove_save(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return

    if not message.text.lstrip("-").isdigit():
        await message.answer("❌ Введите числовой Telegram ID.")
        return

    user_id = int(message.text)
    await state.clear()
    await remove_from_blacklist(user_id)

    await message.answer(
        f"✅ Пользователь <code>{user_id}</code> удалён из чёрного списка.",
        parse_mode="HTML",
        reply_markup=admin_menu_kb(),
    )
    logger.info("Admin %d удалил %d из blacklist", message.from_user.id, user_id)

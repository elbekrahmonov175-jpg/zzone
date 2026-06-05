"""
Хендлер «Связаться с администратором»:
- Пользователь пишет сообщение → оно пересылается всем админам.
- Администратор может ответить пользователю прямо через бота.
"""

import logging
from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config.settings import settings
from keyboards.user_kb import main_menu_kb
from utils.notifications import notify_admins

logger = logging.getLogger(__name__)
router = Router()


class ContactFSM(StatesGroup):
    waiting_message  = State()  # Пользователь пишет вопрос
    waiting_reply    = State()  # Админ вводит ответ пользователю


# ──────────────────────────────────────────────
# ПОЛЬЗОВАТЕЛЬ → АДМИНИСТРАТОР
# ──────────────────────────────────────────────

@router.message(F.text == "💬 Связаться с администратором")
async def contact_admin_start(message: Message, state: FSMContext):
    """Начинает диалог с администратором."""
    await state.set_state(ContactFSM.waiting_message)
    await message.answer(
        "✉️ Напишите ваше сообщение администратору.\n"
        "Он ответит вам в ближайшее время.\n\n"
        "Для отмены напишите /cancel",
    )


@router.message(ContactFSM.waiting_message, F.text)
async def send_message_to_admin(message: Message, state: FSMContext, db_user: dict):
    """Пересылает сообщение пользователя всем администраторам."""
    await state.clear()

    user_text = message.text
    from_user = message.from_user

    # Формируем уведомление для администратора
    admin_text = (
        "📩 <b>Сообщение от пользователя</b>\n\n"
        f"👤 {from_user.full_name}\n"
        f"🔗 @{from_user.username or '—'}\n"
        f"🆔 ID: <code>{from_user.id}</code>\n\n"
        f"💬 {user_text}\n\n"
        f"Чтобы ответить: /reply_{from_user.id}"
    )

    await notify_admins(message.bot, admin_text, parse_mode="HTML")

    await message.answer(
        "✅ Ваше сообщение отправлено администратору!\n"
        "Ожидайте ответа.",
        reply_markup=main_menu_kb(),
    )
    logger.info(
        "Пользователь %d отправил сообщение администратору: %s",
        from_user.id,
        user_text[:50],
    )


# ──────────────────────────────────────────────
# АДМИНИСТРАТОР → ПОЛЬЗОВАТЕЛЬ (ответ)
# ──────────────────────────────────────────────

@router.message(F.text.regexp(r"^/reply_(\d+)$"))
async def admin_reply_start(message: Message, state: FSMContext):
    """Администратор начинает отвечать пользователю."""
    if message.from_user.id not in settings.ADMIN_IDS:
        return

    user_id = int(message.text.split("_")[1])
    await state.set_state(ContactFSM.waiting_reply)
    await state.update_data(reply_to_user_id=user_id)

    await message.answer(
        f"✏️ Введите ответ для пользователя <code>{user_id}</code>:\n"
        "(Для отмены — /cancel)",
        parse_mode="HTML",
    )


@router.message(ContactFSM.waiting_reply, F.text)
async def admin_send_reply(message: Message, state: FSMContext):
    """Отправляет ответ администратора пользователю."""
    if message.from_user.id not in settings.ADMIN_IDS:
        await state.clear()
        return

    data = await state.get_data()
    user_id = data.get("reply_to_user_id")
    await state.clear()

    if not user_id:
        await message.answer("❌ Ошибка: не найден ID пользователя.")
        return

    reply_text = (
        "📬 <b>Ответ от администратора</b>\n\n"
        f"{message.text}"
    )

    try:
        await message.bot.send_message(user_id, reply_text, parse_mode="HTML")
        await message.answer(f"✅ Ответ отправлен пользователю {user_id}.")
        logger.info("Администратор %d ответил пользователю %d", message.from_user.id, user_id)
    except Exception as e:
        await message.answer(f"❌ Не удалось отправить сообщение: {e}")


# ──────────────────────────────────────────────
# ОТМЕНА FSM
# ──────────────────────────────────────────────

@router.message(F.text == "/cancel")
async def cancel_fsm(message: Message, state: FSMContext):
    """Универсальная отмена текущего FSM-состояния."""
    current_state = await state.get_state()
    if current_state:
        await state.clear()
        await message.answer("❌ Действие отменено.", reply_markup=main_menu_kb())
    else:
        await message.answer("Нечего отменять.", reply_markup=main_menu_kb())

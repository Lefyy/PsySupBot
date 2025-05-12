from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StateFilter

from states.form import Form

from keyboards.profile_keyboard import get_profile_inline_keyboard

from db import get_user, add_dialogue_message

from datetime import datetime

profile_router = Router()

@profile_router.message(F.text == "Профиль", ~StateFilter(Form.waiting_for_name))
async def handle_profile_command(message: Message) -> None:
    user = message.from_user
    if not user:
        await message.answer("Произошла ошибка при получении ваших данных пользователя.")
        return

    user_id = user.id
    user_data = get_user(user_id)

    if user_data is None:
        await message.answer("Произошла ошибка при получении данных вашего профиля.")
        return

    full_name = user_data[1]
    # username = user_data[2] # Если хотим показать username
    join_date_str = user_data[3]
    message_balance = user_data[4]

    try:
        join_date = datetime.fromisoformat(join_date_str)
        formatted_join_date = join_date.strftime("%d.%m.%Y %H:%M")
    except (ValueError, TypeError):
        formatted_join_date = "Неизвестно"

    profile_text = (
        f"👤 **Твой профиль:**\n"
        f"Имя: {full_name}\n"
        # f"Username: @{username}\n" if username else "" # Можно добавить username, если есть
        f"Дата присоединения: {formatted_join_date}\n"
        f"Сообщений на балансе: {message_balance}"
    )

    if message.text:
        add_dialogue_message(user_id, message.text, 'user')

    await message.answer(
        profile_text,
        reply_markup=get_profile_inline_keyboard()
    )
    add_dialogue_message(user_id, profile_text, 'bot')

@profile_router.callback_query(F.data == "change_name_profile")
async def handle_change_name_callback(callback_query: CallbackQuery, state: FSMContext) -> None:
    user = callback_query.from_user
    if not user:
         await callback_query.answer("Произошла ошибка при получении ваших данных пользователя.")
         return

    await callback_query.answer("ОК, меняем имя.") # Текст здесь опционален, всплывает как уведомление

    await callback_query.message.answer("Пожалуйста, введи новое имя, которое будет использоваться.")

    await state.set_state(Form.waiting_for_name)
    print(f"Пользователь {user.id} запросил изменение имени. Установлено состояние waiting_for_name.")

    add_dialogue_message(user.id, "Пожалуйста, введи новое имя, которое будет использоваться.", 'bot')
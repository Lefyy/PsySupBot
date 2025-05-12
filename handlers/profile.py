from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StateFilter

from states.form import Form

from keyboards.profile_keyboard import get_profile_inline_keyboard

from db import get_user

from datetime import datetime

profile_router = Router()

@profile_router.message(F.text == "Профиль", ~StateFilter(Form.waiting_for_name))
async def handle_profile_command(message: Message) -> None:
    user = message.from_user
    if not user:
        await message.answer("Произошла ошибка при получении ваших данных пользователя.")
        return

    user_id = user.id
    user_data = get_user(user_id)  # Получаем данные пользователя из БД

    if user_data is None:
        await message.answer("Произошла ошибка при получении данных вашего профиля.")
        return

    full_name = user_data[1]
    join_date_str = user_data[3]
    expiry_date_str = user_data[4]

    try:
        join_date = datetime.fromisoformat(join_date_str)
        formatted_join_date = join_date.strftime("%d.%m.%Y %H:%M")
    except (ValueError, TypeError):
        formatted_join_date = "Неизвестно"

    try:
        expiry_date = datetime.fromisoformat(expiry_date_str)
        formatted_expiry_date = expiry_date.strftime("%d.%m.%Y %H:%M")

        if datetime.now() >= expiry_date:
            subscription_status = "Истекла"
        else:
            subscription_status = f"Активна до {formatted_expiry_date}"
    except (ValueError, TypeError):
        formatted_expiry_date = "Неизвестно"
        subscription_status = "Неизвестно"

    profile_text = (
        f"👤 **Твой профиль:**\n"
        f"Имя: {full_name}\n"
        f"Дата присоединения: {formatted_join_date}\n"
        f"Подписка: {subscription_status}"
    )

    await message.answer(
        profile_text,
        reply_markup=get_profile_inline_keyboard()  # Прикрепляем инлайн-клавиатуру "Изменить имя"
    )

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
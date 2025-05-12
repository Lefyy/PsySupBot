from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from db import add_user, add_dialogue_message, get_user, update_user_name

from keyboards.main_menu import get_main_menu_keyboard
from states.form import Form

start_router = Router()

@start_router.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    user = message.from_user
    if not user:
        await message.answer("Привет! Я бот психологической поддержки. Не могу определить твои данные пользователя.")
        return

    user_id = user.id
    user_in_db = get_user(user_id)

    if user_in_db is None:
        print(f"Новый пользователь: {user_id}")
        add_user(user_id, user.full_name, user.username)

        # Сохраняем первое сообщение /start в диалогах
        if message.text:
             add_dialogue_message(user_id, message.text, 'user')

        await message.answer(
            f"Привет! Я твой бот психологической поддержки. "
            "Прежде чем мы начнем, как я могу к тебе обращаться?\n\n"
            "Пожалуйста, введи имя, которое будет использоваться в нашем общении."
        )

        await state.set_state(Form.waiting_for_name)

    else:
        print(f"Существующий пользователь: {user_id}")
        current_name = user_in_db[1]

        if message.text:
            add_dialogue_message(user_id, message.text, 'user')

        await message.answer(
            f"Снова привет, {current_name}! Чем могу быть полезен сегодня?",
            reply_markup=get_main_menu_keyboard()
        )

        add_dialogue_message(user_id, f"Снова привет, {current_name}! Чем могу быть полезен сегодня?", 'bot')

@start_router.message(Form.waiting_for_name, F.text)
async def process_name(message: Message, state: FSMContext) -> None:
    user = message.from_user
    if not user or not message.text:
         await message.answer("Произошла ошибка при получении имени. Попробуй еще раз или начни с /start.")
         await state.clear() # Сбрасываем состояние
         return

    new_name = message.text.strip()

    if len(new_name) < 2 or len(new_name) > 50:
        await message.answer("Пожалуйста, введи более подходящее имя (от 2 до 50 символов).")
        return

    update_user_name(user.id, new_name)

    add_dialogue_message(user.id, new_name, 'user')

    await message.answer(
        f"Отлично, буду обращаться к тебе {new_name}!",
        reply_markup=get_main_menu_keyboard()
    )

    add_dialogue_message(user.id, f"Отлично, буду обращаться к тебе {new_name}!", 'bot')

    await state.clear()
    print(f"Пользователь {user.id} завершил ввод/изменение имени. Состояние сброшено.")


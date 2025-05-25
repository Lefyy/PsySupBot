from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from db import add_user, get_user, update_user_name

from keyboards.main_menu import get_main_menu_keyboard
from states.form import Form

start_router = Router()

@start_router.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    user = message.from_user
    if not user:
        await message.answer("Ошибка! Не могу определить твои данные пользователя.")
        return

    user_id = user.id
    user_in_db = get_user(user_id)

    if user_in_db is None:
        print(f"Новый пользователь: {user_id}")
        add_user(user_id, user.full_name, user.username)

        await message.answer(
            "👋 Привет! Я — бот-психолог с искусственным интеллектом, который: \n"
            "• Выслушает без осуждения \n"
            "• Поможет разобрать тревогу, стресс или просто плохое настроение \n"
            "• Предложит техники для самопомощи \n\n"
            "📌 Как это работает? \n\n"
            "Пробный период — 1 дней бесплатно. \n"
            "Подписка — после этого всего 189₽/месяц (дешевле кофе с собой). \n\n"
            "👉 Ты можешь: \n"
            "• Попробовать бесплатно — пиши обо всем, что тебя беспокоит в чат прямо сейчас \n"
            "• Сразу оформить подписку — /pay \n\n"
            "P.S. Я не заменяю психотерапевта, но могу поддержать, пока ты ищешь своего специалиста. И да, я не спрашиваю «Как ваши отношения с матерью?»… если ты сам не захочешь об этом поговорить. 😉"
                    )

    else:
        print(f"Существующий пользователь: {user_id}")
        current_name = user_in_db[1]

        await message.answer(
            f"Снова привет, {current_name}! Чем могу быть полезен сегодня?",
            reply_markup=get_main_menu_keyboard()
        )

@start_router.message(Form.waiting_for_name, F.text)
async def process_name(message: Message, state: FSMContext) -> None:
    user = message.from_user
    if not user or not message.text:
         await message.answer("Произошла ошибка при получении имени. Попробуй еще раз или начни с /start.")
         await state.clear()
         return

    new_name = message.text.strip()

    if len(new_name) < 2 or len(new_name) > 50:
        await message.answer("Пожалуйста, введи более подходящее имя (от 2 до 50 символов).")
        return

    update_user_name(user.id, new_name)

    await message.answer(
        f"Отлично, буду обращаться к тебе {new_name}!",
        reply_markup=get_main_menu_keyboard()
    )

    await state.clear()
    print(f"Пользователь {user.id} завершил ввод/изменение имени. Состояние сброшено.")


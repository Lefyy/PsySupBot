from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters.state import StateFilter

from db import add_dialogue_message, get_user, is_subscription_expired
from keyboards.payment_keyboard import get_pay_inline_keyboard

from states.form import Form
from ai_service import get_ai_response

message_router = Router()

@message_router.message(F.text, ~StateFilter(Form.waiting_for_name))
async def handle_all_messages(message: Message) -> None:
    """
    Этот хэндлер отвечает на любые сообщения, кроме команд.
    """
    user = message.from_user
    if not user or not message.text:
        return

    user_id = user.id
    user_text = message.text

    print(f"Получено сообщение от {user.full_name} (ID: {user_id}): {user_text}")

    add_dialogue_message(user_id, user_text, 'user')

    user_data = get_user(user_id)
    if user_data is None:
        await message.answer("Произошла ошибка при получении ваших данных.")
        return

    expiring_date = user_data[4]

    if not is_subscription_expired(user_id):
        print(f"Подписка пользователя {user_id} активна: {expiring_date}. Обрабатываем сообщение AI.")

        ai_response_text = None

        try:
            ai_response_text = await get_ai_response(user_id, user_text)

            if ai_response_text is not None:

                await message.answer(ai_response_text)

                add_dialogue_message(user_id, ai_response_text, 'bot')

            else:
                print(
                    f"AI service returned error or no valid response for user {user_id}. Response: {ai_response_text}")
                await message.answer(
                    "Произошла ошибка при получении ответа от AI. Пожалуйста, попробуй перефразировать или повторить позже.")


        except Exception as e:
            print(f"Неожиданная ошибка при вызове get_ai_response для пользователя {user_id}: {e}")
            await message.answer(
                "Произошла непредвиденная ошибка при обработке вашего запроса. Мы уже работаем над этим.")

    else:
        print(f"Подписка пользователя {user_id} истекла. Просим оплатить.")
        payment_message = "Твоя подписка истекла. Пожалуйста, оплати услугу поддержки, чтобы продолжить общение."
        await message.answer(payment_message,
                             reply_markup=get_pay_inline_keyboard())

@message_router.message(~F.text, ~StateFilter(Form.waiting_for_name))
async def handle_non_text_messages(message: Message) -> None:
     user = message.from_user
     if user:
        print(f"Получено нетекстовое сообщение от {user.full_name} (ID: {user.id}), тип: {message.content_type}")

        await message.answer("Это интересное сообщение! Но пока я умею обрабатывать только текст и команды меню.")
import os
from datetime import datetime
from aiogram import Router, F
# Убедись, что LabeledPrice импортирован отсюда
from aiogram.types import Message, LabeledPrice, SuccessfulPayment, PreCheckoutQuery, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.methods import SendInvoice # Может и не понадобиться, но не помешает

# Импортируем из db.py константу и функции
from db import add_payment, add_dialogue_message, extend_subscription, SUBSCRIPTION_DAYS_PER_PAYMENT

# --- Токен Платежного Провайдера ---
PAYMENTS_PROVIDER_TOKEN = os.getenv("PAYMENTS_PROVIDER_TOKEN")

if not PAYMENTS_PROVIDER_TOKEN:
     print("ВНИМАНИЕ: PAYMENTS_PROVIDER_TOKEN не установлен! Платежи не будут работать.")


payment_router = Router()

# --- Хэндлер для нажатия инлайн-кнопки "Оплатить пакет сообщений" (остается без изменений) ---
@payment_router.callback_query(F.data == "pay_for_subscription")
async def process_pay_button(callback_query: CallbackQuery):
    user = callback_query.from_user
    if not user:
        await callback_query.answer("Произошла ошибка при получении ваших данных пользователя.")
        return

    user_id = user.id

    await callback_query.answer("Переходим к оплате...", show_alert=False)
    print(f"DEBUG: Пользователь {user_id} нажал кнопку Оплатить.")

    price_amount_kopecks = 18900 # 189 RUB = 18900 копеек
    package_description = f"Продление подписки на {SUBSCRIPTION_DAYS_PER_PAYMENT} дней."

    prices = [
        LabeledPrice(label=package_description, amount=price_amount_kopecks),
    ]

    try:
        await callback_query.message.answer_invoice(
            title="Оплата подписки",
            description=package_description,
            payload=f"sub_user_{user_id}_{SUBSCRIPTION_DAYS_PER_PAYMENT}d_{int(datetime.now().timestamp())}",
            provider_token=PAYMENTS_PROVIDER_TOKEN,
            currency="RUB",
            prices=prices,
            start_parameter=f"pay_{user_id}",
        )
        print(f"DEBUG: Пользователю {user_id} отправлен счет на оплату.")

    except Exception as e:
        print(f"DEBUG: Ошибка при отправке счета пользователю {user_id}: {e}")
        await callback_query.message.answer(
            "🛑 Ой-ой! Кажется, платеж заблудился в цифровом пространстве. \n\n"
            "Возможные причины:\n"
            "• Карта притворяется пустой (хотя мы знаем, что это не так) \n"
            "• Банк решил проверить твою решимость \n"
            "• Просто технический глюк (бывает даже у нейросетей) \n\n"
            "Попробуй: \n\n"
            "- Проверить данные карты \n"
            "- Дождаться СМС от банка \n"
            "- Повторить попытку \n"
            "Не переживай - вместе мы победим эту ошибку! 💪 \n"
        )


# --- НОВЫЙ ХЭНДЛЕР: для кнопки "Подписка" из Reply-клавиатуры ---
@payment_router.message(F.text == "Подписка") # Этот хэндлер сработает при нажатии кнопки "Подписка"
async def handle_subscription_button_from_menu(message: Message):
    user = message.from_user
    if not user:
        await message.answer("Произошла ошибка при получении ваших данных пользователя.")
        return

    user_id = user.id

    # Проверяем наличие токена платежного провайдера
    if not PAYMENTS_PROVIDER_TOKEN:
        print("DEBUG: PAYMENTS_PROVIDER_TOKEN не установлен. Невозможно отправить счет.")
        await message.answer("Извините, сейчас невозможно отправить счет на оплату. Пожалуйста, сообщите администратору.")
        return

    # --- Формируем и отправляем счет, аналогично process_pay_button ---
    # Сумма и описание пакета должны совпадать
    price_amount_kopecks = 18900 # 189 RUB = 18900 копеек. Должно совпадать с ценой в инлайн-кнопке!
    package_description = f"Продление подписки на {SUBSCRIPTION_DAYS_PER_PAYMENT} дней."

    prices = [
        LabeledPrice(label=package_description, amount=price_amount_kopecks),
    ]

    try:
        # Используем message.answer_invoice() для отправки счета, так как это Message-хэндлер
        await message.answer_invoice(
            title="Оплата подписки",
            description=package_description,
            payload=f"sub_user_{user_id}_{SUBSCRIPTION_DAYS_PER_PAYMENT}d_{int(datetime.now().timestamp())}",
            provider_token=PAYMENTS_PROVIDER_TOKEN,
            currency="RUB",
            prices=prices,
            start_parameter=f"pay_{user_id}", # Параметр, который будет в команде /start после успешной оплаты
        )
        print(f"DEBUG: Пользователю {user_id} отправлен счет на оплату по нажатию кнопки 'Подписка'.")

    except Exception as e:
        print(f"DEBUG: Ошибка при отправке счета пользователю {user_id} при нажатии кнопки 'Подписка': {e}")
        await message.answer("Произошла ошибка при формировании счета. Попробуйте позже.")


# --- Хэндлер для Pre-Checkout Query (срабатывает ДО оплаты) ---
@payment_router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    user_id = pre_checkout_query.from_user.id
    print(f"DEBUG: Получен Pre-Checkout Query от пользователя {user_id}!")
    print(f"DEBUG: Payload: {pre_checkout_query.invoice_payload}")
    print(f"DEBUG: Сумма: {pre_checkout_query.total_amount / 100} {pre_checkout_query.currency}")

    await pre_checkout_query.answer(ok=True)
    print(f"DEBUG: Pre-Checkout Query для пользователя {user_id} подтвержден (ответ OK).")


# --- Хэндлер для SuccessfulPayment (срабатывает ПОСЛЕ успешной оплаты) ---
@payment_router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    user = message.from_user
    if not user or not message.successful_payment:
         print("DEBUG: Получено невалидное сообщение SuccessfulPayment.")
         return

    user_id = user.id
    payment = message.successful_payment

    print(f"DEBUG: Получено сообщение об успешной оплате от пользователя {user_id}!")
    print(f"DEBUG: Сумма: {payment.total_amount / 100} {payment.currency}")
    print(f"DEBUG: Payload: {payment.invoice_payload}")
    print(f"DEBUG: Telegram Charge ID: {payment.telegram_payment_charge_id}")
    print(f"DEBUG: Provider Charge ID: {payment.provider_payment_charge_id}")

    add_payment(
        user_id=user_id,
        amount=payment.total_amount,
        currency=payment.currency,
        status='successful',
        telegram_charge_id=payment.telegram_payment_charge_id,
        provider_charge_id=payment.provider_payment_charge_id,
        invoice_payload=payment.invoice_payload
    )
    print(f"DEBUG: Информация о платеже для пользователя {user_id} сохранена в БД.")

    days_to_add = SUBSCRIPTION_DAYS_PER_PAYMENT

    new_expiry_date = extend_subscription(user_id, days_to_add)

    if new_expiry_date is not None:
         print(f"DEBUG: Подписка пользователя {user_id} продлена на {days_to_add} дней. Новая дата истечения: {new_expiry_date}.")
         confirmation_message = (
             "🎉 Та-дам! Ты официально прокачал(а) свою психическую броню! \n\n"
             "Теперь в твоем доступе: \n"
             "✓ Все функции без ограничений \n"
             "✓ Персональные рекомендации \n"
             "✓ Возможность сохранять диалоги \n\n"
             "Спасибо, что выбираешь заботу о себе! \n"
             f"Теперь ты среди 17% людей, которые инвестируют в ментальное здоровье. \n" # Просто текст
         )
         await message.answer(confirmation_message)
    else:
         print(f"DEBUG: Ошибка: Не удалось обновить подписку для пользователя {user_id} после успешной оплаты.")
         error_msg = "Оплата получена, но произошла ошибка при обновлении вашей подписки. Пожалуйста, свяжитесь с поддержкой."
         await message.answer(error_msg)
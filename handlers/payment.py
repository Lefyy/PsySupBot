import os
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, LabeledPrice, SuccessfulPayment, PreCheckoutQuery, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton # Импортируем нужные типы
from aiogram.methods import SendInvoice

from db import add_payment, add_dialogue_message, extend_subscription, SUBSCRIPTION_DAYS_PER_PAYMENT # <-- Новые импорты для подписки

# --- Токен Платежного Провайдера ---
# ВАЖНО: Используй тестовый токен от BotFather или провайдера!
# Получить через @BotFather -> /mybots -> твой бот -> Payments -> Connect -> Провайдер -> Тестовый токен
# Или из переменной окружения, например PAYMENTS_PROVIDER_TOKEN
PAYMENTS_PROVIDER_TOKEN = os.getenv("PAYMENTS_PROVIDER_TOKEN") # Пример получения из окружения
# Или захардкоди для теста (НИКОГДА так не делай в продакшене!):
# PAYMENTS_PROVIDER_TOKEN = "284685063:TEST:..." # <-- ЗАМЕНИ НА СВОЙ ТЕСТОВЫЙ ИЛИ ПРОДУКТОВЫЙ ТОКЕН!

if not PAYMENTS_PROVIDER_TOKEN:
     print("ВНИМАНИЕ: PAYMENTS_PROVIDER_TOKEN не установлен! Платежи не будут работать.")


payment_router = Router()

# --- Хэндлер для нажатия инлайн-кнопки "Оплатить пакет сообщений" ---
# Этот хэндлер срабатывает, когда пользователь нажимает кнопку "Оплатить пакет сообщений",
# которую мы показываем, когда подписка истекла.
@payment_router.callback_query(F.data == "pay_for_messages")
async def process_pay_button(callback_query: CallbackQuery):
    user = callback_query.from_user
    if not user:
        await callback_query.answer("Произошла ошибка при получении ваших данных пользователя.")
        return

    user_id = user.id

    # Обязательно отвечаем на CallbackQuery, чтобы убрать индикатор загрузки на кнопке
    # show_alert=False делает уведомление всплывающим, show_alert=True покажет как модальное окно
    await callback_query.answer("Переходим к оплате...", show_alert=False)
    print(f"DEBUG: Пользователь {user_id} нажал кнопку Оплатить.")

    # --- Формируем и отправляем счет ---
    # Здесь можно реализовать выбор разных пакетов услуг, но пока сделаем фиксированный
    # Цена в минимальных единицах валюты (копейки для RUB)
    price_amount = 18900 # 199 RUB = 19900 копеек
    package_description = f"Продление подписки на {SUBSCRIPTION_DAYS_PER_PAYMENT} дней."


    prices = [
        # LabeledPrice - это товарная позиция в счете
        LabeledPrice(label=package_description, amount=price_amount),
    ]

    try:
        await callback_query.message.answer_invoice(
            title="Оплата подписки", # Заголовок счета
            description=package_description, # Описание счета
            # payload - строка для отслеживания платежа, уникальная для каждого счета
            # Можно закодировать ID пользователя, тип пакета, время создания и т.д.
            payload=f"sub_user_{user_id}_{SUBSCRIPTION_DAYS_PER_PAYMENT}d_{int(datetime.now().timestamp())}",
            provider_token=PAYMENTS_PROVIDER_TOKEN, # Тот самый токен провайдера
            currency="RUB", # Валюта (RUB, USD, EUR и т.д.)
            prices=prices,
            start_parameter=f"pay_{user_id}", # Параметр, который будет в команде /start после успешной оплаты (опционально)
            # Опциональные поля, которые могут быть нужны провайдеру или для отображения
            # photo_url="URL_К_КАРТИНКЕ",
            # photo_size=512, photo_width=512, photo_height=512,
            # need_name=False, need_phone_number=False, need_email=False, need_shipping_address=False,
            # is_flexible=False, # True для доставки (не наш случай)
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


# --- Хэндлер для Pre-Checkout Query (срабатывает ДО оплаты) ---
# Telegram отправляет этот запрос после того, как пользователь нажал "Оплатить" в счете,
# но ДО подтверждения платежа в платежной системе.
# Это последний шанс проверить, все ли в порядке с заказом.
@payment_router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    user_id = pre_checkout_query.from_user.id
    print(f"DEBUG: Получен Pre-Checkout Query от пользователя {user_id}!")
    print(f"DEBUG: Payload: {pre_checkout_query.invoice_payload}")
    print(f"DEBUG: Сумма: {pre_checkout_query.total_amount / 100} {pre_checkout_query.currency}")

    # --- Здесь нужно выполнить финальную проверку ---
    # Например:
    # 1. Убедиться, что payload соответствует ожидаемому формату или существующему заказу в твоей системе.
    # 2. Проверить, соответствует ли сумма и валюта ожидаемым.
    # 3. Проверить наличие товара/услуги (в нашем случае услуга всегда доступна).
    # 4. Убедиться, что пользователь имеет право оплачивать (например, не заблокирован).

    # В простом случае, если дополнительных проверок не требуется, просто отвечаем True.
    # Если что-то не так, отвечаем False и указываем причину в error_message.
    await pre_checkout_query.answer(ok=True)
    print(f"DEBUG: Pre-Checkout Query для пользователя {user_id} подтвержден (ответ OK).")

    # Можно сохранить факт получения Pre-Checkout Query в логах или БД для аудита.


# --- Хэндлер для SuccessfulPayment (срабатывает ПОСЛЕ успешной оплаты) ---
# Telegram отправляет обычное сообщение типа SuccessfulPayment после того, как платеж
# успешно прошел в платежной системе.
@payment_router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    user = message.from_user
    if not user or not message.successful_payment:
         print("DEBUG: Получено невалидное сообщение SuccessfulPayment.")
         return # Игнорируем, если нет пользователя или данных платежа

    user_id = user.id
    payment = message.successful_payment

    print(f"DEBUG: Получено сообщение об успешной оплате от пользователя {user_id}!")
    print(f"DEBUG: Сумма: {payment.total_amount / 100} {payment.currency}")
    print(f"DEBUG: Payload: {payment.invoice_payload}")
    print(f"DEBUG: Telegram Charge ID: {payment.telegram_payment_charge_id}")
    print(f"DEBUG: Provider Charge ID: {payment.provider_payment_charge_id}")

    # --- 1. Сохраняем данные платежа в БД ---
    add_payment(
        user_id=user_id,
        amount=payment.total_amount,
        currency=payment.currency,
        status='successful', # Указываем статус "successful"
        telegram_charge_id=payment.telegram_payment_charge_id,
        provider_charge_id=payment.provider_payment_charge_id,
        invoice_payload=payment.invoice_payload
    )
    print(f"DEBUG: Информация о платеже для пользователя {user_id} сохранена в БД.")

    # --- 2. Предоставляем услугу: продлеваем подписку ---
    # Определяем, на сколько дней продлить подписку, исходя из payload или фиксированного значения
    days_to_add = SUBSCRIPTION_DAYS_PER_PAYMENT # Продлеваем на стандартное количество дней

    # Вызываем функцию продления подписки
    new_expiry_date = extend_subscription(user_id, days_to_add)

    if new_expiry_date is not None:
         print(f"DEBUG: Подписка пользователя {user_id} продлена на {days_to_add} дней. Новая дата истечения: {new_expiry_date}.")
         # --- 3. Отправляем пользователю подтверждение и новую дату истечения ---
         confirmation_message = (
             "🎉 Та-дам! Ты официально прокачал(а) свою психическую броню! \n\n"
             "Теперь в твоем доступе: \n"
             "✓ Все функции без ограничений \n"
             "✓ Персональные рекомендации \n"
             "✓ Возможность сохранять диалоги \n\n"
             "Спасибо, что выбираешь заботу о себе! \n"
             "Теперь ты среди 17% людей, которые инвестируют в ментальное здоровье. \n" # Форматируем дату
         )
         await message.answer(confirmation_message)
    else:
         # Если по какой-то причине не удалось обновить подписку в БД
         print(f"DEBUG: Ошибка: Не удалось обновить подписку для пользователя {user_id} после успешной оплаты.")
         error_msg = "Оплата получена, но произошла ошибка при обновлении вашей подписки. Пожалуйста, свяжитесь с поддержкой."
         await message.answer(error_msg)
         # !!! Здесь КРАЙНЕ ВАЖНО УВЕДОМИТЬ АДМИНА о том, что платеж прошел,
         # но услуга не предоставлена, чтобы разобраться вручную!

    # --- 4. Сохраняем сообщение об успешной оплате от Telegram в диалогах ---
    # Само сообщение SuccessfulPayment тоже можно сохранить для логов
    # add_dialogue_message(user_id, "[Telegram: Successful Payment Message]", 'system') # Пример как системное
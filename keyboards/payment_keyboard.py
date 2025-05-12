from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_pay_inline_keyboard():
    """
    Создает и возвращает InlineKeyboardMarkup с кнопкой для оплаты.
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                # callback_data="pay_for_messages" - эти данные мы будем ловить в хэндлере
                InlineKeyboardButton(text="Оплатить пакет сообщений", callback_data="pay_for_messages")
            ]
        ]
    )
    return keyboard
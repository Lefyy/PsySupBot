from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_profile_inline_keyboard():
    """
    Создает и возвращает InlineKeyboardMarkup с кнопкой "Изменить имя".
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [ # Первый и единственный ряд кнопок
                # InlineKeyboardButton требует либо url, либо callback_data, либо другие специфичные параметры
                # callback_data - это данные, которые будут отправлены боту при нажатии
                InlineKeyboardButton(text="Изменить имя", callback_data="change_name_profile")
            ]
        ]
    )
    return keyboard

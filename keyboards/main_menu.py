from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu_keyboard():
    """
    Создает и возвращает ReplyKeyboardMarkup для главного меню.
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [ # Первый ряд кнопок
                KeyboardButton(text="Профиль"), # Кнопка "Профиль"
                KeyboardButton(text="Информация"), # Кнопка "Информация"
            ],
            [
                KeyboardButton(text='Подписка')
            ]
        ],
        resize_keyboard=True, # Сделать клавиатуру компактнее
        one_time_keyboard=False, # Клавиатура не исчезает после нажатия кнопки
    )
    return keyboard
from aiogram.fsm.state import StatesGroup, State

class Form(StatesGroup):
    """
    Класс состояний для конечного автомата (FSM)
    для процессов, связанных с заполнением формы/данных пользователя.
    """
    waiting_for_name = State()
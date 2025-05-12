from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters.state import StateFilter

from states.form import Form

info_router = Router()

@info_router.message(F.text == "Информация", ~StateFilter(Form.waiting_for_name))
async def handle_info_command(message: Message) -> None:
    user = message.from_user
    if user and message.text:
        info_text = "ℹ️ Здесь будет информация о боте, услугах, правилах и т.д."
        await message.answer(info_text)
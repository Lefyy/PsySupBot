from dotenv import load_dotenv

from handlers.payment import payment_router

load_dotenv()

import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from handlers.info import info_router
from handlers.message import message_router
from handlers.profile import profile_router
from handlers.start import start_router

from db import init_db

import os

API_TOKEN = os.getenv('PSY_SUP_API')

async def main():
    bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    dp = Dispatcher()

    dp.include_routers(start_router, info_router, profile_router, payment_router, message_router)

    init_db()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
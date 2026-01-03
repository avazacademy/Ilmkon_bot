import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import start, registration, admin
from database.models import async_main

async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    
    # Bazani yaratish
    await async_main()
    
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    
    dp.include_router(admin.router)
    dp.include_router(start.router)
    dp.include_router(registration.router)

    print("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot to'xtatildi")
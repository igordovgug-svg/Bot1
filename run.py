import asyncio
import os
import logging

from aiogram import Bot, Dispatcher, F

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

from app.handlers import router
from database.engine import create_db, drop_db, session_maker
from middleware.db import DataBaseSession


bot = Bot(token=os.getenv('TOKEN'))
dp = Dispatcher()

dp.include_router(router)


async def on_startup(bot):
    
    run_param = False
    if run_param:
        await drop_db()

    await create_db()


async def on_shutdown(bot):
    print('Bot droped')

async def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    dp.update.middleware(DataBaseSession(session_pool=session_maker))
    
    await create_db()
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Bot stopped')
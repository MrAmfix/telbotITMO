
""" Модуль: main.py
Краткое описание: главный файл, который запускает бота
"""

import asyncio

from aiogram import Dispatcher
from handlers import router, bot


async def main():
    """
        Функция запуска бота
    """
    print('Bot started!')
    dp = Dispatcher()
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print('Bot stopped!')

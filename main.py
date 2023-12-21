
""" Модуль: main.py
Краткое описание: главный файл, который запускает бота
"""

import asyncio

from aiogram import Dispatcher
from utils.logger import logger
from bot.handlers import router, bot
from bot.callbacks import router_callback
from utils.base import init_base


async def main():
    """
        Функция запуска бота
    """
    init_base()
    logger.info('Bot started!')
    dp = Dispatcher()
    dp.include_routers(router, router_callback)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info('Bot stopped!')

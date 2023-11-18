import asyncio

from aiogram import Bot, Dispatcher
from aiogram.enums.parse_mode import ParseMode
from handlers import router
from config import BOT_TOKEN


async def main():
    bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())

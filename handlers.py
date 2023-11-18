from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command


router = Router()


@router.message(Command("start"))
async def handler_start(message: Message):
    await message.reply('Привет, я - бот, который умеет создавать таблицы')



import typing as tp

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery, Message
from config import BOT_TOKEN
from utils import base
from utils.utils import is_chat_admin


def with_registration(func):
    async def checker(*args, **kwargs):
        msg: tp.Union[Message, CallbackQuery] = args[0]
        print(msg)
        if not base.Registration.is_registered(msg.from_user.id):
            await msg.reply('Сначала пройдите регистрацию!')
            return
        return func(*args, **kwargs)
    return checker


def in_chat(func):
    async def checker(*args, **kwargs):
        msg: Message = args[0]
        if msg.chat.type == 'private':
            await msg.reply('Эту команду нельзя использовать в личных сообщениях!')
            return
        return func(*args, **kwargs)
    return checker


def only_admin(func):
    async def checker(*args, **kwargs):
        msg: Message = args[0]
        bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
        if not is_chat_admin(bot.get_chat_administrators(msg.chat.id), msg.from_user.id):
            await msg.reply('У вас нет прав!')
            await bot.session.close()
            return
        await bot.session.close()
        return func(*args, **kwargs)
    return checker

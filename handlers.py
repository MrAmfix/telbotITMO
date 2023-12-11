
""" Модуль: handlers.py
Краткое описание: Этот модуль содержит функции-обработчики команд для бота.
"""

import aiogram.exceptions
import base
import keyboards
import utils
import re

from telebot import TeleBot
from aiogram import Router, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.enums.parse_mode import ParseMode
from aiogram.filters import Command
from config import BOT_TOKEN, FLAGS
from datetime import datetime
from math import ceil

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
router = Router()


@router.message(Command('start'))
async def handler_start(msg: Message):
    """ Обработчик команды /start
        Отправляет приветственное сообщение.
    """
    await msg.reply('Привет, я - бот, который умеет создавать таблицы')


@router.message(Command('reg'))
async def handler_reg(msg: Message):
    """ Обработчик команды /reg
        Регистрирует пользователя в базе данных users или меняет ФИО, если пользователь уже зарегистрирован.
    """
    if re.fullmatch(r'/reg\s[a-zA-Zа-яА-Я]+\s+[a-zA-Zа-яА-Я]+\s*[a-zA-Zа-яА-Я]*', msg.text):
        is_reg = base.Registration.is_registered(msg.from_user.id)
        if is_reg:
            base.Log.logging(f"[RENAME]: user {msg.from_user.id} changed name ({is_reg}) --> ({msg.text[5:]})")
            base.Registration.update_fullname(msg.from_user.id, msg.text[5:])
            await bot.send_message(msg.from_user.id, 'Вы успешно изменили ФИО!')
        else:
            base.Log.logging(f"[REGISTRATION]: user {msg.from_user.id} registered as ({msg.text[5:]})")
            base.Registration.registration(msg.from_user.id, msg.text[5:])
            await bot.send_message(msg.from_user.id, 'Вы успешно зарегистрировались!')
    else:
        await bot.send_message(msg.from_user.id, 'Неправильный формат!')


@router.message(Command('html'))
async def handler_html(msg: Message):
    """ Обработчик команды /html (how to make list)
        Отправляет пользователю сообщение с инструкцией по созданию таблицы.
    """
    instruction = ("*/ml <флаг~> <место>,<дата>,<время начала>,<количество слотов/общая протяженность>,"
                   "<протяженность слота в минутах>*\n\n"
                   "~ - необязательный параметр\n\n"
                   "Какие бывают флаги и что они делают?\n\n\n"
                   "1) -hr  :  Указывает общую протяженность в часах, "
                   "при нецелом количестве ячеек округляет их в большую сторону\n\n"
                   "2) -hd  :  Указывает общую протяженность в часах, "
                   "при нецелом количестве ячеек округляет их в меньшую сторону строну\n\n"
                   "3) -mr  :  Указывает общую протяженность в минутах, "
                   "при нецелом количестве ячеек округляет их в большую сторону\n\n"
                   "4) -md  :  Указывает общую протяженность в минутах, "
                   "при нецелом количестве ячеек округляет их в меньшую сторону строну\n\n"
                   "5) без флага  :  Указывает четвертым параметром количество слотов\n\n\n"
                   "В качестве разделителя параметров необходимо указывать запятую!")
    await bot.send_message(msg.from_user.id, instruction, parse_mode=ParseMode.MARKDOWN)


@router.message(Command('send_logs'))
async def handler_send_logs(msg: Message):
    """ Обработчик команды /send_logs

        КОМАНДА ДОСТУПНА ТОЛЬКО СОЗДАТЕЛЮ БОТА!
        Отправляет создателю глобальные логи.
    """
    if utils.is_bot_creator(msg.from_user.id):
        logs = base.Log.get_global_logs()
        if len(logs) == 0:
            await bot.send_message(msg.from_user.id, 'Логов нет')
        else:
            with open('log.txt', 'w', encoding='utf-8') as file:
                for log in logs:
                    file.write(str(log[0]) + '\n')
            with open('log.txt', 'rb') as file:
                TeleBot(BOT_TOKEN).send_document(msg.from_user.id, file)
    else:
        await bot.send_message(msg.from_user.id, 'У вас нет прав!')


@router.message(Command('logs'))
async def handler_logs(msg: Message):
    """ Обработчик команды /logs

        КОМАНДА ДОСТУПНА ТОЛЬКО АДМИНИСТРАТОРАМ!
        Отправляет логи ячейки, на которую нажмет пользователь следующей.
    """
    if msg.chat.type == 'private':
        await bot.send_message(msg.from_user.id, 'Эту команду нельзя использовать в личных сообщениях!')
        return
    if utils.is_admin(await bot.get_chat_administrators(msg.chat.id), msg.from_user.id):
        if base.Log.set_status(msg.from_user.id):
            await bot.send_message(msg.from_user.id, 'Следующее нажатие на кнопку выдаст вам лог записей на это время')
        else:
            await bot.send_message(msg.from_user.id, 'Для использования этой функции вы должны быть зарегистрированы!')
    else:
        await bot.send_message(msg.from_user.id, 'Вы не являетесь администратором чата!')


@router.message(Command('ml'))
async def pre_handler_ml(msg: Message):
    """ Предварительный обработчик команды /ml

        КОМАНДА ДОСТУПНА ТОЛЬКО АДМИНИСТРАТОРАМ!
        Распознает есть ли в команде флаги и форматирует текст команды для передачи ее в основной обработчик.
    """
    if msg.text.split()[1][0] == '-':
        command = utils.flag_handler(msg.text)
        if command[0] != '/':
            await msg.reply(command)
            return
        await handler_ml(msg, command)
    else:
        await handler_ml(msg, msg.text)


async def handler_ml(msg: Message, text: str):
    """ Обработчик команды /ml
        Создает новую таблицу и отправляет сообщение с клавиатурой для взаимодействия пользователей.
    """
    if msg.chat.type == 'private':
        await msg.reply('Я не делаю таблицы в личных сообщениях')
        return
    if not utils.is_admin(await bot.get_chat_administrators(msg.chat.id), msg.from_user.id):
        await msg.reply('У вас нет прав!')
        return
    datas = list(map(lambda x: x.strip(), text[4:].split(',')))
    if len(datas) != 5:
        await msg.reply('Неправильный формат данных!')
        return
    cd = utils.Formats.check_all(datas[1], datas[2], datas[3], datas[4])
    if cd is not None:
        await msg.reply(cd)
        return
    table_id = base.Select.max_value('table_id', 'table_notes') + 1
    note_id = base.Select.max_value('note_id', 'notes') + 1
    base.Insert.table_into_tables(table_id, msg.from_user.id)
    hours, minutes = int(datas[2][:2]), int(datas[2][3:])
    utils.add_notes(table_id, note_id, int(datas[3]), int(datas[4]), hours, minutes)
    await msg.reply(f'{datas[0]}\n{datas[1]}', reply_markup=keyboards.create_table_keyboard(table_id, 2))


@router.message(Command('add'))
async def pre_handler_add(msg: Message):
    """ Предварительный обработчик команды /add

        КОМАНДА ДОСТУПНА ТОЛЬКО СОЗДАТЕЛЮ ТАБЛИЦЫ!
        Распознает есть ли в команде флаги и форматирует текст команды для передачи ее в основной обработчик.
    """
    if msg.chat.type == 'private':
        await msg.reply('Эта команда не доступна в личных сообщениях')
        return
    elif msg.reply_to_message is None:
        await msg.reply('Вы не переслали сообщение!')
        return
    elif msg.reply_to_message.reply_markup is None:
        await msg.reply('Это сообщение не содержит таблицы!')
        return
    else:
        table_id = msg.reply_to_message.reply_markup.inline_keyboard[0][0].callback_data[4:].split(',')[1]
        if not int(base.Select.creator_id_from_table(table_id)) == msg.from_user.id:
            await msg.reply('Вы не являетесь создателем этой таблицы!')
            return
        if msg.text.split()[1][0] == '-':
            command = utils.flag_handler(msg.text, False)
            if command[0] != '/':
                await msg.reply(command)
                return
            await handler_add(msg, command)
        else:
            await handler_add(msg, msg.text)


async def handler_add(msg: Message, text: str):
    """ Обработчик команды /add

        Добавляет новые ячейки в уже существующую таблицу и обновляет клавиатуру.
    """
    datas = list(map(lambda x: x.strip(), text[5:].split(',')))
    if len(datas) != 3:
        await msg.reply('Неправильный формат!')
        return
    cd = utils.Formats.check_all('01.01.2024', datas[0], datas[1], datas[2])
    if cd is not None:
        await msg.reply(cd)
        return
    table_id = msg.reply_to_message.reply_markup.inline_keyboard[0][0].callback_data[4:].split(',')[1]
    note_id = base.Select.max_value('note_id', 'notes') + 1
    note_old_max = max(list(map(lambda x: int(x), base.Select.notes_from_tables(table_id))))
    time_range = base.Select.note_content_from_notes(note_old_max).time_range[8:]
    if (int(time_range[:2]) * 60 + int(time_range[3:])) > (int(datas[0][:2]) * 60 + int(datas[0][3:])):
        await msg.reply('Временные промежутки пересекаются!')
        return
    else:
        utils.add_notes(int(table_id), note_id, int(datas[1]), int(datas[2]), int(datas[0][:2]), int(datas[0][3:]))
        keyboard = keyboards.create_table_keyboard(table_id, 2)
        await bot.edit_message_text(msg.reply_to_message.text, msg.chat.id,
                                    msg.reply_to_message.message_id, reply_markup=keyboard)
        await bot.send_message(msg.from_user.id, 'Успешно!')


@router.message(Command('replace'))
async def handler_replace(msg: Message):
    """ Обработчик команды /replace

        КОМАНДА ДОСТУПНА ТОЛЬКО АДМИНИСТРАТОРАМ!
        Заменяет место проведения в пересланной таблице.
    """
    if not utils.is_admin(await bot.get_chat_administrators(msg.chat.id), msg.from_user.id):
        await msg.reply('У вас недостаточно прав!')
    elif msg.reply_to_message is None:
        await msg.reply('Вы не переслали сообщение!')
    elif msg.reply_to_message.reply_markup is None:
        await msg.reply('Это сообщение не содержит таблицы!')
    else:
        try:
            await bot.edit_message_text(msg.text[9:] + '\n' + msg.reply_to_message.text.split('\n')[-1],
                                        msg.reply_to_message.chat.id, msg.reply_to_message.message_id,
                                        reply_markup=msg.reply_to_message.reply_markup)
        except aiogram.exceptions.TelegramBadRequest as _ex:
            await msg.reply('Вы указали то же самое место проведения!')


@router.message(Command('info'))
async def handler_info(msg: Message):
    """ Обработчик команды /info

        Пересылает в личные сообщения текстовый вид пересланной таблицы с информацией.
    """
    if msg.reply_to_message is None:
        await msg.reply('Вы не переслали сообщение!')
    elif msg.reply_to_message.reply_markup is None:
        await msg.reply('Это сообщение не содержит таблицы!')
    else:
        table_id = msg.reply_to_message.reply_markup.inline_keyboard[0][0].callback_data[4:].split(',')[1]
        if msg.text == '/info 1' and utils.is_admin(await bot.get_chat_administrators(msg.chat.id), msg.from_user.id):
            await bot.send_message(msg.from_user.id, utils.get_info_table(table_id, True))
        else:
            await bot.send_message(msg.from_user.id, utils.get_info_table(table_id))


@router.message(Command('clear_tables'))
async def handler_clear_tables(msg: Message):
    """ Обработчик команды /clear_tables

        КОМАНДА ДОСТУПНА ТОЛЬКО СОЗДАТЕЛЮ БОТА!
        Очищает таблицы notes и table_notes.
    """
    if not utils.is_bot_creator(msg.from_user.id):
        await bot.send_message(msg.from_user.id, 'У вас нет доступа!')
    else:
        base.clear_tables()
        await bot.send_message(msg.from_user.id, 'Выполнено!')


@router.callback_query()
async def call(callback: CallbackQuery):
    """ Обработчик нажатий на кнопки клавиатур

        Обработчик определяет текст, действие, ID Таблицы и ID ячейки и выполняет инструкции.
        Добавление: добавляет зарегистрированного пользователя в ячейку и обновляет клавиатуру.
        Удаление: проверяет может ли пользователь изменять содержимое ячейки и если да, то удаляет содержимое.
    """
    if not base.Registration.is_registered(callback.from_user.id):
        await bot.send_message(callback.from_user.id, 'Вы не зарегистрированы!')
        return
    if base.Log.get_status(callback.from_user.id) == 1 and \
            utils.is_admin(await bot.get_chat_administrators(callback.message.chat.id), callback.from_user.id):
        base.Log.set_status(callback.from_user.id, 0)
        content = base.Log.get_log_from_note(callback.data[4:].split(',')[0])
        if content == "":
            await bot.send_message(callback.from_user.id, 'Логов нет!')
        else:
            await bot.send_message(callback.from_user.id, f'Логи по запросу:\n\n{content}')
        return
    note_id = callback.data[4:].split(',')[0]
    table_id = callback.data[4:].split(',')[1]
    if callback.data[:4] == 'add_':
        base.Insert.student_into_note(note_id, callback.from_user.id)
        keyboard = keyboards.create_table_keyboard(table_id, 2)
        base.Log.insert_log_into_note(note_id, f'[{datetime.now()}] : '
                                               f'[SUCCESSFUL ADD]: user {callback.from_user.id} added')
        await bot.edit_message_text(f'{callback.message.text}', callback.message.chat.id,
                                    callback.message.message_id, reply_markup=keyboard)
        pass
    elif callback.data[:4] == 'del_':
        student_id = base.Select.student_id_from_note(note_id)
        if student_id is None:
            await bot.send_message(callback.message.chat.id, 'ERROR!!!')
            return
        msg = callback.message
        if utils.is_admin(await bot.get_chat_administrators(msg.chat.id), callback.from_user.id):
            base.Insert.student_into_note(note_id, 'null')
            keyboard = keyboards.create_table_keyboard(table_id, 2)
            base.Log.insert_log_into_note(note_id, f'[{datetime.now()}] : [SUCCESSFUL DEL]: user {student_id} '
                                                   f'was deleted by admin {callback.from_user.id}')
            await bot.edit_message_text(f'{callback.message.text}', callback.message.chat.id,
                                        callback.message.message_id, reply_markup=keyboard)
        elif str(student_id) == str(callback.from_user.id):
            base.Insert.student_into_note(note_id, 'null')
            keyboard = keyboards.create_table_keyboard(table_id, 2)
            base.Log.insert_log_into_note(note_id, f'[{datetime.now()}] : [SUCCESSFUL DEL]: user {student_id}'
                                                   f'delete itself')
            await bot.edit_message_text(f'{callback.message.text}', callback.message.chat.id,
                                        callback.message.message_id, reply_markup=keyboard)
        else:
            await bot.send_message(callback.from_user.id, 'Вы не можете удалить запись!')
    else:
        await bot.send_message(callback.message.chat.id, 'ERROR CALLBACK!!!')

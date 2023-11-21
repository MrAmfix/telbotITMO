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
from config import BOT_TOKEN
from datetime import datetime

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
router = Router()


@router.message(Command('start'))
async def handler_start(msg: Message):
    await msg.reply('Привет, я - бот, который умеет создавать таблицы')


@router.message(Command('reg'))
async def handler_reg(msg: Message):
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
    instruction = ("/ml <место>,<дата>,<время начала>,<количество слотов>,<протяженность слота в минутах>\n\n"
                   "Пример: /ml Ломоносова 1400,01.01.2024,10:00,20,15\n\n"
                   "Обязательно в качестве разделителя ставить запятую.")
    await msg.reply(instruction, parse_mode=ParseMode.MARKDOWN)


@router.message(Command('send_logs'))
async def handler_send_logs(msg: Message):
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
async def handler_ml(msg: Message):
    if msg.chat.type == 'private':
        await msg.reply('Я не делаю таблицы в личных сообщениях')
        return
    if not utils.is_admin(await bot.get_chat_administrators(msg.chat.id), msg.from_user.id):
        await msg.reply('У вас нет прав!')
        return
    datas = list(map(lambda x: x.strip(), msg.text[4:].split(',')))
    if len(datas) != 5:
        await msg.reply('Неправильный формат!')
        return
    if not (re.fullmatch(r'\d{2}.\d{2}.\d{4}', datas[1]) and re.fullmatch(r'\s*\d{2}:\d{2}\s*',
            datas[2]) and datas[3].isnumeric()) or not datas[4].isnumeric():
        await msg.reply('Неправильный формат входных данных!')
        return
    value = utils.is_valid_datas(datas[1], datas[2], int(datas[3]), int(datas[4]))
    if value == -1:
        await msg.reply('Неправильная дата!')
        return
    elif value == -2:
        await msg.reply('Неправильное время начала')
        return
    elif value == -3:
        await msg.reply('Время конечной ячейки для записи превышает 23:59')
        return
    elif value == -4:
        await msg.reply('Количество ячеек не может быть нулем')
        return
    elif value == -5:
        await msg.reply('Интервал не может быть нулем')
        return
    elif value == -6:
        await msg.reply('Не стоит делать столько ячеек (ограничение: 60)')
        return
    table_id = base.Select.max_value('table_id', 'table_notes') + 1
    note_id = base.Select.max_value('note_id', 'notes') + 1
    base.Insert.table_into_tables(table_id, msg.from_user.id)
    hours, minutes = int(datas[2][:2]), int(datas[2][3:])
    utils.add_notes(table_id, note_id, int(datas[3]), int(datas[4]), hours, minutes)
    await msg.reply(f'{datas[0]}\n{datas[1]}', reply_markup=keyboards.create_table_keyboard(table_id, 2))


@router.message(Command('replace'))
async def handler_replace(msg: Message):
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
    if msg.reply_to_message is None:
        await msg.reply('Вы не переслали сообщение!')
    elif not utils.is_admin(await bot.get_chat_administrators(msg.chat.id), msg.from_user.id):
        await msg.reply('У вас недостаточно прав!')
    elif msg.reply_to_message.reply_markup is None:
        await msg.reply('Это сообщение не содержит таблицы!')
    else:
        table_id = msg.reply_to_message.reply_markup.inline_keyboard[0][0].callback_data[4:].split(',')[1]
        await bot.send_message(msg.from_user.id, utils.get_info_table(table_id, msg.text == '/info 1'))


@router.message(Command('clear_tables'))
async def handler_clear_tables(msg: Message):
    if not utils.is_bot_creator(msg.from_user.id):
        await bot.send_message(msg.from_user.id, 'У вас нет доступа!')
    else:
        base.clear_tables()
        await bot.send_message(msg.from_user.id, 'Выполнено!')


@router.callback_query()
async def call(callback: CallbackQuery):
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

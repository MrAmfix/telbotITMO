
""" Модуль: handlers.py
Краткое описание: Этот модуль содержит функции-обработчики команд для бота.
"""

import aiogram.exceptions
import re

from aiogram import Router, Bot
from utils import keyboards, utils, base
from telebot import TeleBot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.enums.parse_mode import ParseMode
from aiogram.filters import Command, StateFilter
from config import BOT_TOKEN
from utils.states import States
from utils.utils import Datas, with_registration


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
            with open('../log.txt', 'w', encoding='utf-8') as file:
                for log in logs:
                    file.write(str(log[0]) + '\n')
            with open('../log.txt', 'rb') as file:
                TeleBot(BOT_TOKEN).send_document(msg.from_user.id, file)
    else:
        await bot.send_message(msg.from_user.id, 'У вас нет прав!')


@with_registration
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


@with_registration
@router.message(Command('ml', 'make_list'))
async def pre_handler_ml(msg: Message):
    """ Предварительный обработчик команды /ml

        КОМАНДА ДОСТУПНА ТОЛЬКО АДМИНИСТРАТОРАМ!
        Распознает есть ли в команде флаги и форматирует текст команды для передачи ее в основной обработчик.
    """
    if re.fullmatch(r'/(ml|make_list)\s*', msg.text):
        await msg.reply('Не указаны данные!')
        return
    if msg.text.split()[1][0] == '-':
        command = utils.flag_handler(msg.text)
        if command[0] != '/':
            await msg.reply(command)
            return
        await handler_ml(msg, command)
    else:
        await handler_ml(msg, msg.text)


async def handler_ml(msg: Message, text: str, edit_id: int = None, edit_mode: bool = False):
    """ Обработчик команды /ml
        Создает новую таблицу и отправляет сообщение с клавиатурой для взаимодействия пользователей.
    """
    if edit_mode:
        uid = edit_id
    else:
        uid = msg.from_user.id
    if msg.chat.type == 'private':
        await msg.reply('Я не делаю таблицы в личных сообщениях')
        return
    if not utils.is_admin(await bot.get_chat_administrators(msg.chat.id), uid):
        await msg.reply('У вас нет прав!')
        return
    datas = list(map(lambda x: x.strip(), text[len(text.split()[0]) + 1:].split(',')))
    if len(datas) != 5:
        await msg.reply('Неправильный формат данных!')
        return
    dataf = Datas(place=datas[0], date=datas[1], time_start=datas[2], count=datas[3], time_range=datas[4])
    cd = utils.Formats.check_all(dataf.date, dataf.time_start, dataf.count, dataf.time_range)
    if cd is not None:
        await msg.reply(cd)
        return
    table_id = base.Select.max_value('table_id', 'table_notes') + 1
    note_id = base.Select.max_value('note_id', 'notes') + 1
    base.Insert.table_into_tables(table_id, uid)
    hours, minutes = int(dataf.time_start[:2]), int(dataf.time_start[3:])
    utils.add_notes(table_id, note_id, int(dataf.count), int(dataf.time_range), hours, minutes)
    if not edit_mode:
        await msg.reply(f'{dataf.place}\n{dataf.date}', reply_markup=keyboards.create_table_keyboard(table_id, 2))
    else:
        await bot.edit_message_text(f'{dataf.place}\n{dataf.date}', msg.chat.id,
                                    msg.message_id, reply_markup=keyboards.create_table_keyboard(table_id, 2))


@router.message(Command('add'))
async def pre_handler_add(msg: Message):
    """ Предварительный обработчик команды /add

        КОМАНДА ДОСТУПНА ТОЛЬКО СОЗДАТЕЛЮ ТАБЛИЦЫ!
        Распознает есть ли в команде флаги и форматирует текст команды для передачи ее в основной обработчик.
    """
    if re.fullmatch(r'/add\s*', msg.text):
        await msg.reply('Не указаны данные!')
        return
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
    datas = list(map(lambda x: x.strip(), text[len(text.split()[0]) + 1:].split(',')))
    if len(datas) != 3:
        await msg.reply('Неправильный формат!')
        return
    dataf = Datas(time_start=datas[0], count=datas[1], time_range=datas[2])
    cd = utils.Formats.check_all('01.01.2024', dataf.time_start, dataf.count, dataf.time_range)
    if cd is not None:
        await msg.reply(cd)
        return
    table_id = msg.reply_to_message.reply_markup.inline_keyboard[0][0].callback_data[4:].split(',')[1]
    note_id = base.Select.max_value('note_id', 'notes') + 1
    note_old_max = max(list(map(lambda x: int(x), base.Select.notes_from_tables(table_id))))
    time_range = base.Select.note_content_from_notes(note_old_max).time_range[8:]
    if (int(time_range[:2]) * 60 + int(time_range[3:])) > (int(dataf.time_start[:2]) * 60 + int(dataf.time_start[3:])):
        await msg.reply('Временные промежутки пересекаются!')
        return
    else:
        utils.add_notes(int(table_id), note_id, int(dataf.count), int(dataf.time_range),
                        int(dataf.time_start[:2]), int(dataf.time_start[3:]))
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
    if msg.chat.type == 'private':
        await msg.reply('Эта команда не доступна в личных сообщениях')
        return
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


@with_registration
@router.message(Command('ct', 'create_temp'))
async def handler_new_template(msg: Message, state: FSMContext):
    """ Обработчик команды /new_template

        Создает шаблон для создания таблицы
        /create_temp <flag~> <time_start>,<count / all_time>,<time_range>
        /ct <~flag> <time_start>,<count / all_time>,<time_range>
    """
    if re.fullmatch(r'/(create_temp|ct)\s*', msg.text):
        await msg.reply('Не указаны данные!')
        return
    if msg.text.split()[1][0] == '-':
        normal_form = (utils.flag_handler(msg.text.replace('ct', 'ml')
                                          .replace('create_temp', 'ml'), with_date=False))
        if normal_form[0] != '/':
            await msg.reply(normal_form)
            return
    else:
        normal_form = (msg.text.replace('ct', 'ml').replace('create_temp', 'ml'))
    datas = list(map(lambda x: x.strip(), normal_form[4:].split(',')))
    if len(datas) != 3:
        await msg.reply('Неправильный формат!')
        return
    v = utils.Formats.check_all('11.11.2023', datas[0], datas[1], datas[2])
    if v is not None:
        await msg.reply(v)
        return
    await msg.reply('Теперь введите ключевое слово, по которому вы будете получать этот шаблон')
    await state.set_state(States.wait_keyword)
    await state.update_data(template_text='/ml ' + ','.join(datas))


@router.message(StateFilter(States.wait_keyword))
async def handler_wait_keyword(msg: Message, state: FSMContext):
    if msg.text.count(' ') > 0:
        await msg.reply('Название шаблона не должно содержать пробелы!')
        return
    get_template = await state.get_data()
    base.Insert.new_template(msg.from_user.id, msg.text, get_template.get('template_text'))
    await msg.reply('Шаблон успешно сохранен!')
    await state.set_state()


@with_registration
@router.message(Command('ml_temp', 'mlt'))
async def handler_make_list_from_template(msg: Message):
    # /ml_temp <place>,<date>
    if re.fullmatch(r'/(ml_temp|mlt)\s*', msg.text):
        await msg.reply('Не указаны данные!')
        return
    if msg.chat.type == 'private':
        await msg.reply('Я не делаю таблицы в личных сообщениях')
        return
    if not utils.is_admin(await bot.get_chat_administrators(msg.chat.id), msg.from_user.id):
        await msg.reply('У вас нет прав!')
        return
    datas = list(map(lambda x: x.strip(), msg.text[len(msg.text.split()[0]) + 1:].split(',')))
    if len(datas) != 2:
        await msg.reply('Неправильный формат данных!')
        return
    if utils.Formats.check_date(datas[1]) is not None:
        await msg.reply(utils.Formats.check_date(datas[1]))
        return
    keyboard = keyboards.create_templates_keyboard(msg.from_user.id, datas[0], datas[1])
    if keyboard is None:
        await msg.reply('У вас нет шаблонов!')
        return
    await msg.reply('Выберите шаблон', reply_markup=keyboard)


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
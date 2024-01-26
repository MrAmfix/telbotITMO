
""" Модуль: handlers.py
Краткое описание: Этот модуль содержит функции-обработчики команд для бота.
"""

import aiogram.exceptions
import re

from aiogram import Router, Bot

from utils import keyboards, utils, base
from telebot import TeleBot
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.enums.parse_mode import ParseMode
from aiogram.filters import Command, StateFilter
from config import BOT_TOKEN, _CALL
from utils.states import States
from utils.utils import Datas


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
            base.Logger.logging(f"[RENAME]: user {msg.from_user.id} changed name ({is_reg}) --> ({msg.text[5:]})")
            base.Registration.update_fullname(msg.from_user.id, msg.text[5:])
            await bot.send_message(msg.from_user.id, 'Вы успешно изменили ФИО!')
        else:
            base.Logger.logging(f"[REGISTRATION]: user {msg.from_user.id} registered as ({msg.text[5:]})")
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
    if not await utils.admission_conditions(msg, is_creator=True):
        return
    logs = base.Logger.get_global_logs()
    if len(logs) == 0:
        await bot.send_message(msg.from_user.id, 'Логов нет')
    else:
        with open('../log.txt', 'w', encoding='utf-8') as file:
            for log in logs:
                file.write(str(log) + '\n')
        with open('../log.txt', 'rb') as file:
            TeleBot(BOT_TOKEN).send_document(msg.from_user.id, file)


@router.message(Command('logs'))
async def handler_logs(msg: Message):
    """ Обработчик команды /logs

        КОМАНДА ДОСТУПНА ТОЛЬКО АДМИНИСТРАТОРАМ!
        Отправляет логи ячейки, на которую нажмет пользователь следующей.
    """
    if not await utils.admission_conditions(msg, is_reg=True):
        return
    if base.Logger.set_status(msg.from_user.id):
        await bot.send_message(msg.from_user.id, 'Следующее нажатие на кнопку выдаст вам лог записей на это время')


@router.message(Command('ml', 'make_list'))
async def pre_handler_ml(msg: Message):
    """ Предварительный обработчик команды /ml

        КОМАНДА ДОСТУПНА ТОЛЬКО АДМИНИСТРАТОРАМ!
        Распознает есть ли в команде флаги и форматирует текст команды для передачи ее в основной обработчик.
    """
    if not await utils.admission_conditions(msg, is_reg=True, is_chat=True):
        return
    if len(msg.text.split()) == 1:
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
    datas = list(map(lambda x: x.strip(), text[len(text.split()[0]) + 1:].split(',')))
    if len(datas) != 5:
        await msg.reply('Неправильный формат данных!')
        return
    dataf = Datas(place=datas[0], date=datas[1], time_start=datas[2], count=datas[3], time_range=datas[4])
    cd = utils.Formats.check_all(dataf.date, dataf.time_start, dataf.count, dataf.time_range)
    if cd is not None:
        await msg.reply(cd)
        return
    table_id = base.Insert.table_into_tables(uid)
    hours, minutes = int(dataf.time_start[:2]), int(dataf.time_start[3:])
    await utils.add_notes(table_id, int(dataf.count), int(dataf.time_range), hours, minutes)
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
    if not await utils.admission_conditions(msg, is_reg=True, is_chat=True):
        return
    if len(msg.text.split()) == 1:
        await msg.reply('Не указаны данные!')
        return
    elif msg.reply_to_message is None:
        await msg.reply('Вы не переслали сообщение!')
        return
    elif msg.reply_to_message.reply_markup is None:
        await msg.reply('Это сообщение не содержит таблицы!')
        return
    else:
        if msg.reply_to_message.reply_markup.inline_keyboard[0][0].callback_data[:4] not in ['add_', 'del_']:
            await msg.reply('Это не таблица!')
            return
        table_id = msg.reply_to_message.reply_markup.inline_keyboard[0][0].callback_data[4:].split(_CALL)[1]
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
    if len(msg.reply_to_message.reply_markup.inline_keyboard) * len(
            msg.reply_to_message.reply_markup.inline_keyboard[0]) + int(dataf.count) > 60:
        await msg.reply('Не стоит делать такие большие таблицы (Ограничение: 60)!')
        return
    cd = utils.Formats.check_all('01.01.2024', dataf.time_start, dataf.count, dataf.time_range)
    if cd is not None:
        await msg.reply(cd)
        return
    table_id = msg.reply_to_message.reply_markup.inline_keyboard[0][0].callback_data[4:].split(_CALL)[1]
    note_old_max = max(list(map(lambda x: int(x), base.Select.notes_from_tables(table_id))))
    time_range = base.Select.note_content_from_notes(note_old_max).time_range[8:]
    if (int(time_range[:2]) * 60 + int(time_range[3:])) > (int(dataf.time_start[:2]) * 60 + int(dataf.time_start[3:])):
        await msg.reply('Временные промежутки пересекаются!')
        return
    else:
        await utils.add_notes(int(table_id), int(dataf.count), int(dataf.time_range),
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
    if not await utils.admission_conditions(msg, is_chat=True):
        return
    elif msg.reply_to_message is None:
        await msg.reply('Вы не переслали сообщение!')
    elif msg.reply_to_message.reply_markup is None:
        await msg.reply('Это сообщение не содержит таблицы!')
    elif msg.reply_to_message.reply_markup.inline_keyboard[0][0].callback_data[:4] not in ['add_', 'del_']:
        await msg.reply('Это не таблица!')
        return
    else:
        try:
            await bot.edit_message_text(msg.text[9:].strip() + '\n' + msg.reply_to_message.text.split('\n')[-1],
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
    elif msg.reply_to_message.reply_markup.inline_keyboard[0][0].callback_data[:4] not in ['add_', 'del_']:
        await msg.reply('Это не таблица!')
        return
    else:
        table_id = msg.reply_to_message.reply_markup.inline_keyboard[0][0].callback_data[4:].split(_CALL)[1]
        if msg.text == '/info 1' and await utils.admission_conditions(msg, is_chat=True):
            await bot.send_message(msg.from_user.id, utils.get_info_table(table_id, True))
        else:
            await bot.send_message(msg.from_user.id, utils.get_info_table(table_id))


@router.message(Command('ctt', 'create_table_template'))
async def handler_new_template(msg: Message, state: FSMContext):
    """ Обработчик команды /ctt

        Создает шаблон для создания таблицы
        /create_table_template <flag~> <time_start>,<count / all_time>,<time_range>
        /ctt <~flag> <time_start>,<count / all_time>,<time_range>
    """
    if not await utils.admission_conditions(msg, is_reg=True):
        return
    if len(msg.text.split()) == 1:
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
    get_template = await state.get_data()
    base.Insert.new_template(msg.from_user.id, msg.text, get_template.get('template_text'))
    await msg.reply('Шаблон успешно сохранен!')
    await state.set_state()


@router.message(Command('cpt', 'create_place_template'))
async def handler_create_place_template(msg: Message):
    if not await utils.admission_conditions(msg, is_reg=True):
        return
    if len(msg.text.split()) == 1:
        await msg.reply('Не указаны данные!')
        return
    await bot.send_message(msg.from_user.id, f'Успешно добавлен шаблон места: {msg.text.split(maxsplit=1)[1]}')
    base.Insert.new_place_template(msg.from_user.id, msg.text.split(maxsplit=1)[1])


@router.message(Command('mlt', 'ml_temp'))
async def handler_make_list_from_temp(msg: Message, state: FSMContext):
    # /mlt <place>,<date>
    # /mlt
    if not await utils.admission_conditions(msg, is_reg=True, is_chat=True):
        return
    if base.Select.user_templates(msg.from_user.id) is None:
        await msg.reply('У вас нет шаблонов!')
        return
    if re.fullmatch(r'/(mlt|ml_temp)(@notes_itmo_beta_bot)*\s*', msg.text):
        # /mlt
        places = base.Select.place_templates(msg.from_user.id)
        keyboard = keyboards.create_places_table_keyboard(places)
        await msg.reply(f'Введите{"" if places is None else " или выберите"} место проведения', reply_markup=keyboard)
        await state.set_state(States.wait_place)
    else:
        # /mlt <place>,<date>
        datas = [x.strip() for x in msg.text.split(maxsplit=1)[1].split(',')]
        if len(datas) != 2:
            await msg.reply('Неправильный формат данных!')
            return
        if utils.Formats.check_date(datas[1]) is not None:
            await msg.reply(utils.Formats.check_date(datas[1]))
            return
        keyboard = keyboards.create_templates_keyboard(msg.from_user.id, datas[0], datas[1])
        await msg.reply('Выберите шаблон', reply_markup=keyboard)


@router.message(StateFilter(States.wait_place))
async def handler_wait_place(msg: Message, state: FSMContext):
    await msg.reply('Введите или выберите дату проведения', reply_markup=keyboards.create_dates_keyboard())
    await state.update_data(place=msg.text)
    await state.set_state(States.wait_date)


@router.message(StateFilter(States.wait_date))
async def handler_wait_date(msg: Message, state: FSMContext):
    if utils.Formats.check_date(msg.text) is not None:
        await msg.reply(utils.Formats.check_date(msg.text), reply_markup=ReplyKeyboardRemove())
        await state.set_state()
    else:
        gd = await state.get_data()
        await state.set_state()
        await msg.reply('Выберите шаблон', reply_markup=ReplyKeyboardRemove())
        await msg.reply('ᅠ ᅠ', reply_markup=keyboards.create_templates_keyboard(
            msg.from_user.id, gd.get('place'), msg.text))

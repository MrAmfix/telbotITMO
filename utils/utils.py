
""" Модуль: utils.py
Краткое описание: Этот модуль содержит вспомогательные классы и функции.
"""


import re
import typing as tp

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery
from utils import base
from config import ID_OWNER, FLAGS, BOT_TOKEN
from datetime import datetime
from math import ceil


class Note:
    """
        Класс для удобного хранения информации о ячейке.

        :param time_range: Временной промежуток.
        :param student_id: ID студента или None, если никто не записан в ячейку.
    """

    def __init__(self, time_range: str, student_id: tp.Union[str, int, None]):
        self.time_range = time_range
        self.student_id = student_id


class Datas:
    """
        Класс для удобного хранения данных при создании / редактировании таблиц
    """
    def __init__(self, place: str = None, date: str = None, time_start: str = None,
                 count: tp.Union[str, int, None] = None, time_range: tp.Union[str, int, None] = None):
        self.place = place
        self.date = date
        self.time_start = time_start
        self.count = count
        self.time_range = time_range


class Formats:
    """
    Класс для проверки корректности данных для создания / дополнения таблиц
    """
    @staticmethod
    def check_date(date: str) -> tp.Optional[str]:
        try:
            datetime.strptime(date, '%d.%m.%Y')
            return None
        except ValueError:
            return 'Неправильная дата'

    @staticmethod
    def check_time_start(time_start: str) -> tp.Optional[str]:
        if not re.fullmatch(r'\d{2}:\d{2}', time_start):
            return 'Неправильное время!'
        if not (0 <= int(time_start.strip()[:2]) < 24 and 0 <= int(time_start.strip()[3:]) < 60):
            return 'Неправильное время!'
        return None

    @staticmethod
    def check_count(count: str) -> tp.Optional[str]:
        if not count.isnumeric():
            return 'Неправильный формат данных!'
        if int(count) == 0:
            return 'Количество ячеек не может быть нулем!'
        if int(count) > 60:
            return 'Не стоит делать столько ячеек (ограничение: 60)!'
        return None

    @staticmethod
    def check_time_range(time_range: str) -> tp.Optional[str]:
        if not time_range.isnumeric():
            return 'Неправильный формат данных!'
        if int(time_range) == 0:
            return 'Интервал не может быть нулем!'
        return None

    @staticmethod
    def check_all(date: str, time_start: str, count: str, time_range: str) -> tp.Optional[str]:
        v1, v2, v3, v4 = (Formats.check_date(date), Formats.check_time_start(time_start),
                          Formats.check_count(count), Formats.check_time_range(time_range))
        if v1 is not None:
            return v1
        if v2 is not None:
            return v2
        if v3 is not None:
            return v3
        if v4 is not None:
            return v4
        if (int(time_start[:2]) * 60 + int(time_start[3:]) + int(count) * int(time_range)) >= 1440:
            return 'Время конечной записи превышает 23:59!'
        return None


def is_chat_admin(admin_list, user_id: tp.Union[str, int]) -> bool:
    # admin_list = await bot.get_chat_administrators(msg.chat.id)
    """
        Проверяет, является ли пользователь администратором чата.

        :param admin_list: Список администраторов чата.
        :param user_id: ID пользователя.

        :return: True, если пользователь администратор, иначе False.
    """
    admins = [str(user.user.id) for user in admin_list]
    return str(user_id) in admins


def is_bot_creator(user_id: int) -> bool:
    """
        Проверяет, является ли пользователь создателем бота.

        :param user_id: ID пользователя.

        :return: True, если пользователь является создателем бота, иначе False.
    """
    if user_id == int(ID_OWNER):
        return True
    return False


def flag_handler(msg: str, with_date: bool = True) -> str:
    """
    Переводит команду с флагом в стандартный формат

    :param msg: команда с флагом
    :param with_date: True - строка с датой, False - без даты

    :return: команда в стандартном формате, либо сообщение об ошибке
    """
    tag_command = msg.split()[0]
    flag = msg.split()[1][1:]
    if flag in FLAGS:
        if with_date:
            ind = 3
            datas = list(map(lambda x: x.strip(), msg[len(tag_command):].strip().split(',')))
        else:
            ind = 1
            datas = list(map(lambda x: x.strip(), msg[len(tag_command):].strip().split(',')))
        datas[0] = datas[0][len(flag) + 1:].strip()
        if len(datas) != (ind + 2):
            return 'Неправильный формат!'
        elif not datas[ind].isnumeric() or not datas[ind + 1].isnumeric():
            return 'Неправильный формат входных данных!'
        else:
            if int(datas[ind]) == 0 or int(datas[ind + 1]) == 0:
                return 'Неправильный формат входных данных!'
            if flag == 'hr':
                datas[ind] = str(ceil(int(datas[ind]) * 60 / int(datas[ind + 1])))
            elif flag == 'hd':
                datas[ind] = str(int(datas[ind]) * 60 // int(datas[ind + 1]))
            elif flag == 'mr':
                datas[ind] = str(ceil(int(datas[ind]) / int(datas[ind + 1])))
            elif flag == 'md':
                datas[ind] = str(int(datas[ind]) // int(datas[ind + 1]))
            return tag_command + ' ' + ','.join(datas)
    else:
        return 'Некорректный флаг!'


def add_notes(table_id: int, start_note_id: int, count: int, time_range: int, hours: int, minutes: int):
    """
    Вставляет ячейки с временными промежутками в таблицу table_notes.

    :param table_id: ID таблицы, куда нужно вставить ячейки.
    :param start_note_id: ID начальной ячейки.
    :param count: Количество ячеек.
    :param time_range: Временной промежуток.
    :param hours: Часы начала.
    :param minutes: Минуты начала.
    """
    for note_id in range(start_note_id, start_note_id + count):
        range_time = f"{'{:02}'.format(hours)}:{'{:02}'.format(minutes)} - "
        hours += (minutes + time_range) // 60
        minutes = (minutes + time_range) % 60
        range_time += f"{'{:02}'.format(hours)}:{'{:02}'.format(minutes)}"
        base.Insert.note_into_notes(note_id, range_time)
        base.Insert.note_into_table(note_id, table_id)


def get_info_table(table_id: tp.Union[int, str], debug: bool = False) -> str:
    """
        Возвращает информацию о заметках в таблице.

        :param table_id: ID таблицы.
        :param debug: Включен ли режим отладки (по умолчанию False).

        :return: Информация о содержимом таблицы.
    """
    notes = base.Select.notes_from_tables(table_id)
    info = ""
    if debug:
        info += f'[table_id : {table_id}]\n\n'
    for note in notes:
        note_content = base.Select.note_content_from_notes(note)
        if debug:
            info += f'[note_id : {note}] '
        info += f'{note_content.time_range} : '
        if note_content.student_id is None:
            info += 'пусто\n'
        else:
            info += f'{base.Select.fullname_from_users(note_content.student_id)}'
            if debug:
                info += f' (id: {note_content.student_id})'
            info += '\n'
    return info


async def admission_conditions(msg: tp.Union[Message, CallbackQuery] = None, is_reg: bool = False,
                               is_chat: bool = False,
                               is_admin: bool = False,
                               is_creator: bool = False) -> bool:
    call: CallbackQuery
    if is_reg:
        if not base.Registration.is_registered(msg.from_user.id):
            bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
            await bot.send_message(msg.from_user.id, 'Сначала пройдите регистрацию!')
            await bot.session.close()
            return False
    if is_chat:
        if msg.chat.type == 'private':
            await msg.reply('Эту команду нельзя использовать в личных сообщениях!')
            return False
    if is_admin:
        bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
        if not is_chat_admin(await bot.get_chat_administrators(msg.chat.id), msg.from_user.id):
            await msg.reply('Вы не являетесь администратором!')
            await bot.session.close()
            return False
        await bot.session.close()
    if is_creator:
        if not is_bot_creator(msg.from_user.id):
            await msg.reply('Вы не являетесь создателем бота!')
            return False
    return True

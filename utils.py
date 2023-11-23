
""" Модуль: utils.py
Краткое описание: Этот модуль содержит вспомогательные классы и функции.
"""

import base

from config import ID_OWNER
from datetime import datetime


class Note:
    """
        Класс для удобного хранения информации о ячейке.

        :param time_range: Временной промежуток.
        :param student_id: ID студента или None, если никто не записан в ячейку.
    """
    def __init__(self, time_range: str, student_id: str | int | None):
        self.time_range = time_range
        self.student_id = student_id


def is_admin(admin_list, user_id: int | str) -> bool:
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


def is_valid_datas(date: str, time: str, count: int, time_range: int):
    """ Функция, проверяющая входные данные для создания таблицы.

    :param date: Дата в формате dd.mm.yyyy.
    :param time: Время начала в формате hh:mm.
    :param count: Количество ячеек.
    :param time_range: Временной промежуток в минутах.

    Значения return:
        -1 : неправильная дата
        -2 : неправильное время начала
        -3 : время окончания превышает 23:59
        -4 : количество записей - 0
        -5 : недопустимый интервал
        -6 : слишком много ячеек
         1 : входные данные корректны
    """

    def is_valid_date(dates):
        try:
            datetime.strptime(dates, '%d.%m.%Y')
            return True
        except ValueError:
            return False

    if not is_valid_date(date.strip()):
        return -1
    if not (0 <= int(time.strip()[:2]) < 24 and 0 <= int(time.strip()[3:]) < 60):
        return -2
    time_end = int(time.strip()[:2]) * 60 + int(time.strip()[3:]) + count * time_range
    if time_end >= 1440:
        return -3
    if count == 0:
        return -4
    if time_range == 0:
        return -5
    if count > 60:
        return -6
    return 1


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


def get_info_table(table_id: int | str, debug: bool = False) -> str:
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
                info += f' (id: {base.Select.fullname_from_users(note_content.student_id)})'
            info += '\n'
    return info

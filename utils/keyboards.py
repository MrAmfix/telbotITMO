
""" Модуль: keyboards.py
Краткое описание: Этот модуль содержит функции создания клавиатур.
"""

import typing as tp

from utils import base
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import _CALL


def create_table_keyboard(table_id: tp.Union[int, str], width: int = 1) -> InlineKeyboardMarkup:
    """
        Создает клавиатуру с встроенными кнопками для работы с ячейками в таблице.

        :param table_id: ID таблицы.
        :param width: Количество кнопок в одной строке клавиатуры (по умолчанию 1).

        :return: InlineKeyboardMarkup: Объект клавиатуры с встроенными кнопками.
    """
    buttons = []
    buttons_format = []
    for note in base.Select.notes_from_tables(table_id):
        note_content = base.Select.note_content_from_notes(note)
        if note_content.student_id is None:
            buttons.append(InlineKeyboardButton(text=f'{note_content.time_range}',
                                                callback_data=f'add_{note}{_CALL}{table_id}'))
        else:
            buttons.append(InlineKeyboardButton(text=f'🔒 {note_content.time_range}\n'
                                                     f'{base.Select.fullname_from_users(note_content.student_id)}',
                                                callback_data=f'del_{note}{_CALL}{table_id}'))
    i = 0
    buttons_format.append([])
    for button in buttons:
        buttons_format[-1].append(button)
        i += 1
        if i == width:
            i = 0
            buttons_format.append([])
    return InlineKeyboardMarkup(inline_keyboard=buttons_format)


def create_templates_keyboard(user_id: tp.Union[int, str], place: str, date: str,
                              width: int = 2) -> tp.Optional[InlineKeyboardMarkup]:
    temps = base.Select.user_templates(user_id)
    if temps is None:
        return None
    buttons = []
    buttons_format = []
    for key in temps.keys():
        id_key = base.Insert.value_into_dict(f'{user_id}{_CALL}{key}{_CALL}{place}{_CALL}{date}')
        buttons.append(InlineKeyboardButton(text=f'{key}',
                                            callback_data=f'temp{id_key}'))
        print(len(f'temp{user_id}{_CALL}{key}{_CALL}{place}{_CALL}{date}'.encode('utf-8')))
        print(len(f'temp{id_key}'.encode('utf-8')))
    i = 0
    buttons_format.append([])
    for button in buttons:
        buttons_format[-1].append(button)
        i += 1
        if i == width:
            i = 0
            buttons_format.append([])
    return InlineKeyboardMarkup(inline_keyboard=buttons_format)


def create_confirm_template_keyboard(user_id: tp.Union[int, str], key: str, place: str,
                                     date: str) -> InlineKeyboardMarkup:
    buttons = [[]]
    id_key = base.Insert.value_into_dict(f'{user_id}{_CALL}{place}{_CALL}{date}')
    buttons[-1].append(InlineKeyboardButton(text='Назад',
                                            callback_data=f'back{id_key}'))
    id_key = base.Insert.value_into_dict(f'{user_id}{_CALL}{key}{_CALL}{place}{_CALL}{date}')
    buttons[-1].append(InlineKeyboardButton(text='Подтвердить',
                                            callback_data=f'conf{id_key}'))
    return InlineKeyboardMarkup(inline_keyboard=buttons)

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import base


def create_table_keyboard(table_id: int | str, width: int = 1):
    buttons = []
    buttons_format = []
    for note in base.Select.notes_from_tables(table_id):
        note_content = base.Select.note_content_from_notes(note)
        if note_content.student_id is None:
            buttons.append(InlineKeyboardButton(text=f'{note_content.time_range}',
                                                callback_data=f'add_{note},{table_id}'))
        else:
            buttons.append(InlineKeyboardButton(text=f'🔒 {note_content.time_range}\n'
                                                     f'{base.Select.fullname_from_users(note_content.student_id)}',
                                                callback_data=f'del_{note},{table_id}'))
    i = 0
    buttons_format.append([])
    for button in buttons:
        buttons_format[-1].append(button)
        i += 1
        if i == width:
            i = 0
            buttons_format.append([])
    return InlineKeyboardMarkup(inline_keyboard=buttons_format)

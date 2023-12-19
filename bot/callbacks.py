
""" Модуль callbacks.py
Краткое описание: Этот модуль содержит функции-обработчики нажатий
"""

from datetime import datetime

from aiogram import Router
from aiogram.types import CallbackQuery
from bot.handlers import handler_ml, bot
from utils import base, utils, keyboards
from utils.utils import with_registration
from config import _CALL


router_callback = Router()


@with_registration
@router_callback.callback_query()
async def call(callback: CallbackQuery):
    """ Обработчик нажатий на кнопки клавиатур

        Обработчик определяет текст, действие, ID Таблицы и ID ячейки и выполняет инструкции.
        Добавление: добавляет зарегистрированного пользователя в ячейку и обновляет клавиатуру.
        Удаление: проверяет может ли пользователь изменять содержимое ячейки и если да, то удаляет содержимое.
    """
    if base.Log.get_status(callback.from_user.id) == 1 and \
            utils.is_admin(await bot.get_chat_administrators(callback.message.chat.id), callback.from_user.id):
        base.Log.set_status(callback.from_user.id, 0)
        content = base.Log.get_log_from_note(callback.data[4:].split(_CALL)[0])
        if content == "":
            await bot.send_message(callback.from_user.id, 'Логов нет!')
        else:
            await bot.send_message(callback.from_user.id, f'Логи по запросу:\n\n{content}')
        return

    # Callback.data должна быть в формате <info><other_info>, где <info> состоит из 4 символов

    if callback.data[:4] == 'add_':
        note_id = callback.data[4:].split(_CALL)[0]
        table_id = callback.data[4:].split(_CALL)[1]
        base.Insert.student_into_note(note_id, callback.from_user.id)
        keyboard = keyboards.create_table_keyboard(table_id, 2)
        base.Log.insert_log_into_note(note_id, f'[{datetime.now()}] : '
                                               f'[SUCCESSFUL ADD]: user {callback.from_user.id} added')
        await bot.edit_message_text(f'{callback.message.text}', callback.message.chat.id,
                                    callback.message.message_id, reply_markup=keyboard)
        pass
    elif callback.data[:4] == 'del_':
        note_id = callback.data[4:].split(_CALL)[0]
        table_id = callback.data[4:].split(_CALL)[1]
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
    elif callback.data[:4] == 'temp':
        datas = callback.data[4:].split(_CALL)
        # temp{user_id}{_CALL}{key}{_CALL}{place}{_CALL}{date}
        if datas[0] == str(callback.from_user.id):
            keyboard = keyboards.create_confirm_template_keyboard(*datas)
            datas_temp = base.Select.user_templates(datas[0])[datas[1]][4:].split(',')
            new_text = (f'Время начала: {datas_temp[0]}\n'
                        f'Количество слотов: {datas_temp[1]}\n'
                        f'Время на слов: {datas_temp[2]} минут')
            await bot.edit_message_text(new_text, callback.message.chat.id,
                                        callback.message.message_id, reply_markup=keyboard)
    elif callback.data[:4] == 'back':
        datas = callback.data[4:].split(_CALL)
        # back{user_id}{_CALL}{place}{_CALL}{date}
        if datas[0] == str(callback.from_user.id):
            keyboard = keyboards.create_templates_keyboard(*datas)
            await bot.edit_message_text('Выберите шаблон', callback.message.chat.id,
                                        callback.message.message_id, reply_markup=keyboard)
    elif callback.data[:4] == 'conf':
        datas = callback.data[4:].split(_CALL)
        # conf{user_id}{_CALL}{key}{_CALL}{place}{_CALL}{date}
        if datas[0] == str(callback.from_user.id):
            datas_temp = base.Select.user_templates(datas[0])[datas[1]]
            await handler_ml(callback.message, f'{datas_temp[:4]}{datas[2]},{datas[3]},{datas_temp[4:]}',
                             callback.from_user.id, True)
    else:
        await bot.send_message(callback.message.chat.id, 'ERROR CALLBACK!!!')

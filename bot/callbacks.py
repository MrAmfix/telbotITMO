""" Модуль callbacks.py
Краткое описание: Этот модуль содержит функции-обработчики нажатий
"""

from datetime import datetime

from aiogram import Router
from aiogram.types import CallbackQuery
from bot.handlers import handler_ml, bot
from utils import utils, keyboards, base
from config import _CALL

router_callback = Router()


@router_callback.callback_query()
async def call(callback: CallbackQuery):
    """ Обработчик нажатий на кнопки клавиатур

        Обработчик определяет текст, действие, ID Таблицы и ID ячейки и выполняет инструкции.
        Добавление: добавляет зарегистрированного пользователя в ячейку и обновляет клавиатуру.
        Удаление: проверяет может ли пользователь изменять содержимое ячейки и если да, то удаляет содержимое.
    """
    if not await utils.admission_conditions(callback, is_reg=True):
        return
    if base.Logger.get_status(callback.from_user.id) == 1 and utils.admission_conditions(is_admin=True, is_reg=True):
        base.Logger.set_status(user_id=callback.from_user.id, value=0)
        content = base.Logger.get_log_from_note(callback.data[4:].split(_CALL)[0])
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
        base.Logger.insert_log_into_note(note_id, f'[{datetime.now()}] : '
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
        if utils.is_chat_admin(await bot.get_chat_administrators(msg.chat.id), callback.from_user.id):
            base.Insert.student_into_note(note_id, None)
            keyboard = keyboards.create_table_keyboard(table_id, 2)
            base.Logger.insert_log_into_note(note_id, f'[{datetime.now()}] : [SUCCESSFUL DEL]: user {student_id} '
                                                      f'was deleted by admin {callback.from_user.id}')
            await bot.edit_message_text(f'{callback.message.text}', callback.message.chat.id,
                                        callback.message.message_id, reply_markup=keyboard)
        elif str(student_id) == str(callback.from_user.id):
            base.Insert.student_into_note(note_id, None)
            keyboard = keyboards.create_table_keyboard(table_id, 2)
            base.Logger.insert_log_into_note(note_id, f'[{datetime.now()}] : [SUCCESSFUL DEL]: user {student_id}'
                                                      f'delete itself')
            await bot.edit_message_text(f'{callback.message.text}', callback.message.chat.id,
                                        callback.message.message_id, reply_markup=keyboard)
        else:
            await bot.send_message(callback.from_user.id, 'Вы не можете удалить запись!')
    elif callback.data[:4] == 'temp':
        id_key = int(callback.data[4:])
        datas = base.Select.value_from_dict(id_key)
        datas = datas.split(_CALL)
        # {user_id}{_CALL}{key}{_CALL}{place}{_CALL}{date}
        if datas[0] == str(callback.from_user.id):
            keyboard = keyboards.create_confirm_template_keyboard(*datas)
            datas_temp = base.Select.user_templates(datas[0])[datas[1]][4:].split(',')
            time_end = int(datas_temp[0][:2]) * 60 + int(datas_temp[0][3:]) + int(datas_temp[1]) * int(datas_temp[2])
            time_end = f"{'{:02}'.format(time_end // 60)}:{'{:02}'.format(time_end % 60)}"
            new_text = (f'Время начала: {datas_temp[0]}\n'
                        f'Время конца: {time_end}\n'
                        f'Количество слотов: {datas_temp[1]}\n'
                        f'Время на слот: {datas_temp[2]} минут')
            await bot.edit_message_text(new_text, callback.message.chat.id,
                                        callback.message.message_id, reply_markup=keyboard)
    elif callback.data[:4] == 'back':
        id_key = int(callback.data[4:])
        datas = base.Select.value_from_dict(id_key)
        datas = datas.split(_CALL)
        # {user_id}{_CALL}{place}{_CALL}{date}
        if datas[0] == str(callback.from_user.id):
            keyboard = keyboards.create_templates_keyboard(*datas)
            await bot.edit_message_text('Выберите шаблон', callback.message.chat.id,
                                        callback.message.message_id, reply_markup=keyboard)
    elif callback.data[:4] == 'conf':
        id_key = int(callback.data[4:])
        datas = base.Select.value_from_dict(id_key)
        datas = datas.split(_CALL)
        # {user_id}{_CALL}{key}{_CALL}{place}{_CALL}{date}
        if datas[0] == str(callback.from_user.id):
            datas_temp = base.Select.user_templates(datas[0])[datas[1]]
            await handler_ml(callback.message, f'{datas_temp[:4]}{datas[2]},{datas[3]},{datas_temp[4:]}',
                             callback.from_user.id, True)
    else:
        await bot.send_message(callback.message.chat.id, 'ERROR CALLBACK!!!')

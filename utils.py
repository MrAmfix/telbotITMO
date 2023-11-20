import base
from config import ID_OWNER
from datetime import datetime


def is_admin(admin_list, user_id: int | str) -> bool:
    admins = [str(user.user.id) for user in admin_list]
    return str(user_id) in admins


def is_bot_creator(user_id: int) -> bool:
    if user_id == int(ID_OWNER):
        return True
    return False


def is_valid_datas(date: str, time: str, count: int, time_range: int):
    """ Функция, проверяющая входные данные для создания таблицы

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
    for note_id in range(start_note_id, start_note_id + count):
        range_time = f"{'{:02}'.format(hours)}:{'{:02}'.format(minutes)} - "
        hours += (minutes + time_range) // 60
        minutes = (minutes + time_range) % 60
        range_time += f"{'{:02}'.format(hours)}:{'{:02}'.format(minutes)}"
        base.Insert.note_into_notes(note_id, range_time)
        base.Insert.note_into_table(note_id, table_id)


""" Модуль: base.py
Краткое описание: Этот модуль содержит классы и функции для взаимодействия с базой данных PostgreSQL.
"""

import psycopg2
import typing as tp

from config import DB_PORT, DB_HOST, DB_PASS, DB_USER, DB_NAME
from utils.logger import logger
from utils.utils import CNote
from datetime import datetime


connect = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT)
connect.autocommit = True


def init_base():
    with open('init.sql', 'r') as file:
        queries = file.read().split(';')
        with connect.cursor() as cursor:
            for query in queries:
                cursor.execute(query)


class Registration:
    """
        Класс: Registration
        Краткое описание: Предоставляет методы для регистрации пользователя и смены имени.
    """

    @staticmethod
    def registration(user_id: tp.Union[str, int], full_name: str):
        """
            Регистрирует нового пользователя в таблице users.

            :param user_id: ID пользователя.
            :param full_name: ФИО пользователя.
        """
        with connect.cursor() as cursor:
            cursor.execute(f'''INSERT INTO users (user_id, full_name) VALUES (\'{user_id}\',\'{full_name}\')''')

    @staticmethod
    def update_fullname(user_id: tp.Union[int, str], full_name: str):
        """
            Обновляет ФИО существующего пользователя в таблице users.

            :param user_id: ID пользователя.
            :param full_name: Новое ФИО пользователя.
        """
        with connect.cursor() as cursor:
            cursor.execute(f'''UPDATE users SET full_name = \'{full_name}\' WHERE user_id = \'{user_id}\'''')

    @staticmethod
    def is_registered(user_id: tp.Union[int, str]) -> tp.Union[str, bool]:
        """
            Проверяет, зарегистрирован ли пользователь.

            :param user_id: ID пользователя.
            :return: ФИО пользователя, если зарегистрирован, в противном случае False.
        """
        with connect.cursor() as cursor:
            cursor.execute(f'''SELECT full_name FROM users WHERE user_id = \'{user_id}\'''')
            full_name = cursor.fetchone()
            if full_name is not None:
                return str(full_name[0])
            return False


class Logger:
    """ Класс: Log
        Краткое описание: Предоставляет методы для вставки и получения логов ячеек / общих логов.
    """

    @staticmethod
    def logging(text: str):
        """
            Записывает глобальный лог с меткой времени в таблице 'logs'.

            :param text: Текст.
        """
        with connect.cursor() as cursor:
            cursor.execute(f'''INSERT INTO logs (log_text) VALUES (\'[{datetime.now()}] : {text}\')''')

    @staticmethod
    def insert_log_into_note(note_id: tp.Union[int, str], log: str):
        """
            Вставляет лог в журнал конкретной ячейки.

            :param note_id: ID ячейки.
            :param log: Текст для вставки.
        """
        with connect.cursor() as cursor:
            cursor.execute(f'''UPDATE notes SET logs = array_append(logs, \'{log}\') 
            WHERE note_id = {note_id}''')

    @staticmethod
    def get_global_logs() -> tp.Optional[list]:
        """
            Получает все глобальные логи из таблицы 'logs'.

            :return: Список глобальных логов или None, если записей нет.
        """
        with connect.cursor() as cursor:
            cursor.execute('''SELECT log_text FROM logs''')
            return cursor.fetchall()

    @staticmethod
    def get_log_from_note(note_id: tp.Union[int, str]) -> str:
        """
            Получает логи, связанные с конкретной ячейкой.

            :param note_id: ID ячейки.
            :return: Отформатированная строка с логами или пустая строка, если записей нет.
        """
        with connect.cursor() as cursor:
            cursor.execute(f'''SELECT logs FROM notes WHERE note_id = {note_id}''')
            data = cursor.fetchone()[0]
            if data is None:
                return ""
            data_string = ""
            for cd in data:
                data_string += (cd + '\n\n')
            return data_string

    @staticmethod
    def get_status(user_id: tp.Union[int, str]) -> int:
        """
            Получает состояние (is_check_logs) пользователя.

            :param user_id: ID пользователя.
            :return: Состояние пользователя (0 или 1).
        """
        if not Registration.is_registered(user_id):
            return 0
        with connect.cursor() as cursor:
            cursor.execute(f'''SELECT is_check_logs FROM users WHERE user_id = \'{user_id}\'''')
            return int(cursor.fetchone()[0])

    @staticmethod
    def set_status(user_id: tp.Union[int, str], value: int = 1) -> bool:
        """
            Устанавливает состояние (is_check_logs) пользователя.

            :param user_id: ID пользователя.
            :param value: Значение для установки (по умолчанию 1).
            :return: True, если статус успешно установлен, в противном случае False.
        """
        if not Registration.is_registered(user_id):
            return False
        with connect.cursor() as cursor:
            cursor.execute(f'''UPDATE users SET is_check_logs = {value} WHERE user_id = \'{user_id}\'''')
            return True


class Select:
    """ Класс: Select
        Краткое описание: Предоставляет методы для получения информации из таблиц.
    """

    @staticmethod
    def max_value(column: str, table: str) -> tp.Optional[int]:
        """
            Получает максимальное значение из указанного столбца таблицы.

            :param column: Столбец, из которого извлекается максимальное значение.
            :param table: Таблица, в которой производится поиск максимального значения.
            :return: Максимальное значение или None, если произошла ошибка.
        """
        try:
            with connect.cursor() as cursor:
                cursor.execute(f'''SELECT MAX({column}) FROM {table}''')
                return int(cursor.fetchone()[0])
        except Exception as _ex:
            logger.info(f'ERROR: {_ex}')
            return None

    @staticmethod
    def notes_from_tables(table_id: tp.Union[int, str]) -> list:
        """
            Получает список ID ячеек, связанных с конкретной таблицей.

            :param table_id: ID таблицы.
            :return: Список ID ячеек.
        """
        with connect.cursor() as cursor:
            cursor.execute(f'''SELECT notes_id FROM table_notes WHERE table_id = {table_id}''')
            return cursor.fetchone()[0]

    @staticmethod
    def note_content_from_notes(note_id: tp.Union[int, str]) -> CNote:
        """
            Получает информацию о временном промежутке и ID студента из конкретной ячейки.

            :param note_id: ID ячейки.
            :return: Экземпляр класса Note, содержащий временной промежуток и ID студента.
        """
        with connect.cursor() as cursor:
            cursor.execute(f'''SELECT time_range, student_id FROM notes WHERE note_id = {note_id}''')
            content = list(cursor.fetchone())
            return CNote(content[0], content[1])

    @staticmethod
    def fullname_from_users(user_id: tp.Union[int, str]) -> tp.Optional[str]:
        """
            Получает ФИО пользователя.

            :param user_id: ID пользователя.
            :return: ФИО пользователя или None, если пользователь не зарегистрирован.
        """
        try:
            with connect.cursor() as cursor:
                cursor.execute(f'''SELECT full_name FROM users WHERE user_id = \'{user_id}\'''')
                return cursor.fetchone()[0]
        except Exception as _ex:
            logger.info(f'ERROR: {_ex}')
            return None

    @staticmethod
    def creator_id_from_table(table_id: tp.Union[int, str]) -> tp.Optional[str]:
        """
            Получает ID создателя таблицы.

            :param table_id: ID таблицы.
            :return: ID создателя таблицы или None, если таблицы не существует.
        """
        try:
            with connect.cursor() as cursor:
                cursor.execute(f'''SELECT creator_id FROM table_notes WHERE table_id = {table_id}''')
                return cursor.fetchone()[0]
        except Exception as _ex:
            logger.info(f'ERROR: {_ex}')
            return None

    @staticmethod
    def student_id_from_note(note_id: tp.Union[int, str]) -> tp.Optional[str]:
        """
            Получает ID студента, записавшегося в конкретную ячейку.

            :param note_id: ID ячейки.
            :return: ID студента или None, если никто не записался в ячейку.
        """
        with connect.cursor() as cursor:
            cursor.execute(f'''SELECT student_id FROM notes WHERE note_id = {note_id}''')
            uid = cursor.fetchone()
            if uid is not None:
                return uid[0]
            return None

    @staticmethod
    def user_templates(user_id: tp.Union[int, str]) -> tp.Optional[dict]:
        """
            Получает словарь шаблонов, созданных пользователем

            :param user_id: ID пользователя
            :return: словарь или None (при отсутствии шаблонов)
        """
        with connect.cursor() as cursor:
            cursor.execute(f'''SELECT templates FROM users WHERE user_id = \'{user_id}\'''')
            templates = cursor.fetchone()[0]
            if templates is not None:
                return dict(templates)
            return None

    @staticmethod
    def value_from_dict(dict_key: int) -> tp.Optional[str]:
        with connect.cursor() as cursor:
            cursor.execute(f'''SELECT dict_value FROM dict WHERE dict_key = {dict_key}''')
            return cursor.fetchone()[0]


class Insert:
    """ Класс: Insert
        Краткое описание: Предоставляет методы для вставки информации в таблицы.
    """

    @staticmethod
    def table_into_tables(table_id: tp.Union[int, str], creator_id: tp.Union[int, str]):
        """
            Вставляет новую запись в таблицу 'table_notes'.

            :param table_id: ID таблицы.
            :param creator_id: ID создателя.
        """
        with connect.cursor() as cursor:
            cursor.execute(f'''INSERT INTO table_notes (table_id, creator_id) 
            VALUES ({table_id}, \'{creator_id}\')''')

    @staticmethod
    def note_into_notes(note_id: tp.Union[int, str], time_range: str):
        """
            Вставляет новую запись в таблицу 'notes'.

            :param note_id: ID ячейки.
            :param time_range: Временной промежуток.
        """
        with connect.cursor() as cursor:
            cursor.execute(f'''INSERT INTO notes (note_id, time_range) VALUES 
                            ({note_id}, \'{time_range}\')''')

    @staticmethod
    def note_into_table(note_id: tp.Union[int, str], table_id: tp.Union[int, str]):
        """
            Вставляет ячейку в конкретную таблицу.

            :param note_id: ID ячейки.
            :param table_id: ID таблицы.
        """
        with connect.cursor() as cursor:
            cursor.execute(f'''UPDATE table_notes SET notes_id = array_append(notes_id, {note_id}) 
            WHERE table_id = {table_id}''')

    @staticmethod
    def student_into_note(note_id: tp.Union[str, int], student_id: tp.Union[str, int]):
        """
            Вставляет ID студента в конкретную ячейку.

            :param note_id: ID ячейки.
            :param student_id: ID студента.
        """
        with connect.cursor() as cursor:
            if student_id == 'null':
                cursor.execute(f'''UPDATE notes SET student_id = null 
                WHERE note_id = {note_id}''')
            else:
                cursor.execute(f'''UPDATE notes SET student_id = \'{student_id}\' 
                WHERE note_id = {note_id}''')

    @staticmethod
    def new_template(user_id: tp.Union[str, int], keyword: str, template: str):
        """
            Вставляет шаблон, созданный пользователем

            :param user_id: ID пользователя
            :param keyword: Ключевое слово для получения шаблона
            :param template: Текст шаблона
        """
        with connect.cursor() as cursor:
            if Select.user_templates(user_id) is None:
                cursor.execute(f'''update users set templates = '{{\"{keyword}\":
                 \"{template}\"}}' where user_id = \'{user_id}\'''')
            else:
                cursor.execute(f'''update users set templates = jsonb_set(templates, \'{{{keyword}}}\',
                 \'\"{template}\"\', TRUE) WHERE user_id = \'{user_id}\'''')

    @staticmethod
    def value_into_dict(value: str) -> int:
        with connect.cursor() as cursor:
            id = Select.max_value('dict_key', 'dict') + 1
            cursor.execute(f'''INSERT INTO dict (dict_key, dict_value) VALUES ({id}, \'{value}\')''')
            return id


def clear_tables():
    """
        Очищает таблицы notes и table_notes в базе данных.
    """
    pass
    # with connect.cursor() as cursor:
    #     cursor.execute(f'''TRUNCATE notes, table_notes;
    #      INSERT INTO notes (note_id) VALUES (0);
    #      INSERT INTO table_notes (table_id) VALUES (0);''')


def get_users():
    with connect.cursor() as cursor:
        cursor.execute(f'''SELECT * FROM users''')
        string = ''
        for i in cursor.fetchall():
            string += f'{i}\n'
    return string



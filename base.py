import psycopg2

from config import DB_PORT, DB_HOST, DB_PASS, DB_USER, DB_NAME
from datetime import datetime


connect = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT)
connect.autocommit = True


class Registration:
    @staticmethod
    def registration(user_id: int | str, full_name: str):
        with connect.cursor() as cursor:
            cursor.execute(f'''INSERT INTO users (user_id, full_name) VALUES (\'{user_id}\',\'{full_name}\')''')

    @staticmethod
    def update_fullname(user_id: int | str, full_name: str):
        with connect.cursor() as cursor:
            cursor.execute(f'''UPDATE users SET full_name = \'{full_name}\' WHERE user_id = \'{user_id}\'''')

    @staticmethod
    def is_registered(user_id: int | str) -> str | bool:
        with connect.cursor() as cursor:
            cursor.execute(f'''SELECT full_name FROM users WHERE user_id = \'{user_id}\'''')
            full_name = cursor.fetchone()
            if full_name is not None:
                return str(full_name[0])
            return False


class Log:
    @staticmethod
    def logging(text):
        with connect.cursor() as cursor:
            cursor.execute(f'''INSERT INTO logs (log_text) VALUES (\'[{datetime.now()}] : {text}\')''')

    @staticmethod
    def insert_log_into_note(note_id: int | str, log: str):
        with connect.cursor() as cursor:
            cursor.execute(f'''UPDATE notes SET logs = array_append(logs, \'{log}\') 
            WHERE note_id = {note_id}''')

    @staticmethod
    def get_global_logs():
        with connect.cursor() as cursor:
            cursor.execute('''SELECT log_text FROM logs''')
            return cursor.fetchall()

    @staticmethod
    def get_log_from_note(note_id: int | str) -> str:
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
    def get_status(user_id: int | str) -> int:
        if not Registration.is_registered(user_id):
            return 0
        with connect.cursor() as cursor:
            cursor.execute(f'''SELECT is_check_logs FROM users WHERE user_id = \'{user_id}\'''')
            return int(cursor.fetchone()[0])

    @staticmethod
    def set_status(user_id: int | str, value: int = 1) -> bool:
        if not Registration.is_registered(user_id):
            return False
        with connect.cursor() as cursor:
            cursor.execute(f'''UPDATE users SET is_check_logs = {value} WHERE user_id = \'{user_id}\'''')
            return True


class Select:
    @staticmethod
    def max_value(column: str, table: str) -> int | None:
        try:
            with connect.cursor() as cursor:
                cursor.execute(f'''SELECT MAX({column}) FROM {table}''')
                return int(cursor.fetchone()[0])
        except Exception as _ex:
            return None

    @staticmethod
    def notes_from_tables(table_id: int | str) -> list:
        with connect.cursor() as cursor:
            cursor.execute(f'''SELECT notes_id FROM table_notes WHERE table_id = {table_id}''')
            return cursor.fetchone()[0]

    @staticmethod
    def note_content_from_notes(note_id: int | str) -> list:
        with connect.cursor() as cursor:
            cursor.execute(f'''SELECT time_range, student_id FROM notes WHERE note_id = {note_id}''')
            return list(cursor.fetchone())

    @staticmethod
    def fullname_from_users(user_id: int | str) -> str | None:
        try:
            with connect.cursor() as cursor:
                cursor.execute(f'''SELECT full_name FROM users WHERE user_id = \'{user_id}\'''')
                return cursor.fetchone()[0]
        except Exception as _ex:
            return None

    @staticmethod
    def student_id_from_note(note_id: int | str) -> str | None:
        with connect.cursor() as cursor:
            cursor.execute(f'''SELECT student_id FROM notes WHERE note_id = {note_id}''')
            uid = cursor.fetchone()
            if uid is not None:
                return uid[0]
            return None


class Insert:
    @staticmethod
    def table_into_tables(table_id: int | str, creator_id: int | str):
        with connect.cursor() as cursor:
            cursor.execute(f'''INSERT INTO table_notes (table_id, creator_id) 
            VALUES ({table_id}, \'{creator_id}\')''')

    @staticmethod
    def note_into_notes(note_id: int | str, time_range: str):
        with connect.cursor() as cursor:
            cursor.execute(f'''INSERT INTO notes (note_id, time_range) VALUES 
                            ({note_id}, \'{time_range}\')''')

    @staticmethod
    def note_into_table(note_id: int | str, table_id: int | str):
        with connect.cursor() as cursor:
            cursor.execute(f'''UPDATE table_notes SET notes_id = array_append(notes_id, {note_id}) 
            WHERE table_id = {table_id}''')

    @staticmethod
    def student_into_note(note_id: int | str, student_id: int | str):
        with connect.cursor() as cursor:
            if student_id == 'null':
                cursor.execute(f'''UPDATE notes SET student_id = null 
                WHERE note_id = {note_id}''')
            else:
                cursor.execute(f'''UPDATE notes SET student_id = \'{student_id}\' 
                WHERE note_id = {note_id}''')

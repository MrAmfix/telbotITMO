import typing as tp

from utils.models import User, TableNote, Note, Log, Dict, Base
from config import DB_PORT, DB_HOST, DB_PASS, DB_USER, DB_NAME, DB_ADAPTER
from utils.logger import logger
from utils.utils import CNote
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

path = f"{DB_ADAPTER}://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(f'{path}')
Base.metadata.create_all(engine)


class Registration:
    @staticmethod
    def registration(user_id: tp.Union[str, int], full_name: str) -> None:
        with sessionmaker(bind=engine)() as session:
            session.add(User(user_id=user_id, full_name=full_name))
            session.commit()

    @staticmethod
    def update_fullname(user_id: tp.Union[int, str], full_name: str) -> None:
        with sessionmaker(bind=engine)() as session:
            user = session.query(User).filter_by(user_id=user_id).first()
            if user:
                user.full_name = full_name
                session.commit()

    @staticmethod
    def is_registered(user_id: tp.Union[int, str]) -> tp.Union[str, bool]:
        with sessionmaker(bind=engine)() as session:
            user = session.query(User).filter_by(user_id=user_id).first()
            return str(user.full_name) if user else False


class Logger:
    @staticmethod
    def logging(text: str) -> None:
        with sessionmaker(bind=engine)() as session:
            session.add(Log(log_text=f'[{datetime.now()}] : {text}'))
            session.commit()

    @staticmethod
    def insert_log_into_note(note_id: tp.Union[int, str], log: str) -> None:
        with sessionmaker(bind=engine)() as session:
            note = session.query(Note).filter_by(note_id=note_id).first()
            if note:
                note.logs.append(log)
                session.commit()

    @staticmethod
    def get_global_logs() -> tp.Optional[list]:
        with sessionmaker(bind=engine)() as session:
            logs = session.query(Log).all()
            return [log.log_text for log in logs] if logs else None

    @staticmethod
    def get_log_from_note(note_id: tp.Union[int, str]) -> str:
        with sessionmaker(bind=engine)() as session:
            note = session.query(Note).filter_by(note_id=note_id).first()
            return '\n\n'.join(note.logs) if (note and note.logs) else ""

    @staticmethod
    def get_status(user_id: tp.Union[int, str]) -> int:
        with sessionmaker(bind=engine)() as session:
            if not Registration.is_registered(user_id):
                return 0
            return int(session.query(User).filter_by(user_id=user_id).first().is_check_logs)

    @staticmethod
    def set_status(user_id: tp.Union[int, str], value: int = 1) -> bool:
        with sessionmaker(bind=engine)() as session:
            if not Registration.is_registered(user_id):
                return False
            user = session.query(User).filter_by(user_id=user_id).first()
            user.is_check_logs = value
            session.commit()
            return True


class Select:
    @staticmethod
    def max_value(column: str, table: str) -> tp.Optional[int]:

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

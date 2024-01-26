import typing as tp


from utils.models import User, TableNote, Note, Log, Dict, Base
from config import DB_PORT, DB_HOST, DB_PASS, DB_USER, DB_NAME, DB_ADAPTER
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

path = f"{DB_ADAPTER}://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(f'{path}')
Base.metadata.create_all(engine)


class CNote:
    def __init__(self, time_range: str, student_id: tp.Union[str, int, None]):
        self.time_range = time_range
        self.student_id = student_id


def with_session(func):
    def wrapper(*args, **kwargs):
        with sessionmaker(bind=engine)() as session:
            return func(session, *args, **kwargs)
    return wrapper


class Registration:
    @staticmethod
    @with_session
    def registration(session: Session, user_id: tp.Union[str, int], full_name: str) -> None:
        session.add(User(user_id=str(user_id), full_name=full_name))
        session.commit()

    @staticmethod
    @with_session
    def update_fullname(session: Session, user_id: tp.Union[str, int], full_name: str) -> None:
        user = session.query(User).filter_by(user_id=str(user_id)).first()
        if user:
            user.full_name = full_name
            session.commit()

    @staticmethod
    @with_session
    def is_registered(session: Session, user_id: tp.Union[int, str]) -> tp.Union[str, bool]:
        user = session.query(User).filter_by(user_id=str(user_id)).first()
        return str(user.full_name) if user else False


class Logger:
    @staticmethod
    @with_session
    def logging(session: Session, text: str) -> None:
        txt = f'[{datetime.now()}] : {text}'
        session.add(Log(log_text=txt))
        session.commit()

    @staticmethod
    @with_session
    def insert_log_into_note(session: Session, note_id: tp.Union[int, str], log: str) -> None:
        note = session.query(Note).filter_by(note_id=note_id).first()
        if note.logs is not None:
            note.logs.append(log)
        else:
            note.logs = [log]
        session.commit()

    @staticmethod
    @with_session
    def get_global_logs(session: Session) -> tp.Optional[tp.List[str]]:
        logs = session.query(Log).all()
        return [str(log.log_text) for log in logs] if logs else []

    @staticmethod
    @with_session
    def get_log_from_note(session: Session, note_id: tp.Union[int, str]) -> str:
        note = session.query(Note).filter_by(note_id=int(note_id)).first()
        return '\n\n'.join(note.logs) if (note and note.logs) else ""

    @staticmethod
    @with_session
    def get_status(session: Session, user_id: tp.Union[int, str]) -> int:
        if not Registration.is_registered(user_id):
            return 0
        return int(session.query(User).filter_by(user_id=str(user_id)).first().is_check_logs)

    @staticmethod
    @with_session
    def set_status(session: Session, user_id: tp.Union[int, str], value: int = 1) -> bool:
        if not Registration.is_registered(user_id):
            return False
        user = session.query(User).filter_by(user_id=str(user_id)).first()
        user.is_check_logs = value
        session.commit()
        return True


class Select:
    @staticmethod
    @with_session
    def notes_from_tables(session: Session, table_id: tp.Union[int, str]) -> list:
        table = session.query(TableNote).filter_by(table_id=int(table_id)).first()
        return table.notes_id

    @staticmethod
    @with_session
    def note_content_from_notes(session: Session, note_id: tp.Union[int, str]) -> CNote:
        note = session.query(Note).filter_by(note_id=int(note_id)).first()
        return CNote(note.time_range, note.student_id)

    @staticmethod
    @with_session
    def fullname_from_users(session: Session, user_id: tp.Union[int, str]) -> tp.Optional[str]:
        user = session.query(User).filter_by(user_id=str(user_id)).first()
        if user is not None:
            return user.full_name
        return None

    @staticmethod
    @with_session
    def creator_id_from_table(session: Session, table_id: tp.Union[int, str]) -> tp.Optional[str]:
        table = session.query(TableNote).filter_by(table_id=int(table_id)).first()
        if table is not None:
            return table.creator_id
        return None

    @staticmethod
    @with_session
    def student_id_from_note(session: Session, note_id: tp.Union[int, str]) -> tp.Optional[str]:
        uid = session.query(Note).filter_by(note_id=int(note_id)).first().student_id
        if uid is not None:
            return str(uid)
        return None

    @staticmethod
    @with_session
    def user_templates(session: Session, user_id: tp.Union[int, str]) -> tp.Optional[dict]:
        return session.query(User).filter_by(user_id=str(user_id)).first().templates

    @staticmethod
    @with_session
    def value_from_dict(session: Session, dict_key: int) -> tp.Optional[str]:
        return session.query(Dict).filter_by(dict_key=dict_key).first().dict_value

    @staticmethod
    @with_session
    def place_templates(session: Session, user_id: tp.Union[str, int]) -> tp.Optional[tp.List[str]]:
        pt = session.query(User).filter_by(user_id=str(user_id)).first().place_templates
        if pt is not None:
            return [str(place) for place in pt]
        return None


class Insert:
    @staticmethod
    @with_session
    def table_into_tables(session: Session, creator_id: tp.Union[int, str]) -> int:
        #  def new_table -> table_id
        new_table = TableNote(creator_id=str(creator_id))
        session.add(new_table)
        session.commit()
        session.flush()
        return new_table.table_id

    @staticmethod
    @with_session
    def note_into_notes(session: Session, time_range: str) -> int:
        #  new note -> note_id
        new_note = Note(time_range=time_range)
        session.add(new_note)
        session.commit()
        session.flush()
        return int(new_note.note_id)

    @staticmethod
    @with_session
    def note_into_table(session: Session, note_id: tp.Union[int, str], table_id: tp.Union[int, str]):
        table = session.query(TableNote).filter_by(table_id=table_id).first()
        if table.notes_id is None:
            table.notes_id = [note_id]
        else:
            table.notes_id = [*table.notes_id, note_id]
        session.flush()
        session.commit()

    @staticmethod
    @with_session
    def student_into_note(session: Session, note_id: tp.Union[str, int], student_id: tp.Optional[tp.Union[str, int]]):
        note = session.query(Note).filter_by(note_id=int(note_id)).first()
        if student_id is None:
            note.student_id = None
        else:
            note.student_id = str(student_id)
        session.commit()

    @staticmethod
    @with_session
    def new_template(session: Session, user_id: tp.Union[str, int], keyword: str, template: str):
        user = session.query(User).filter_by(user_id=str(user_id)).first()
        if user.templates is None:
            user.templates = {keyword: template}
        else:
            user.templates = {**user.templates, keyword: template}
        session.commit()

    @staticmethod
    @with_session
    def value_into_dict(session: Session, value: str) -> int:
        new_values = Dict(dict_value=value)
        session.add(new_values)
        session.commit()
        return new_values.dict_key

    @staticmethod
    @with_session
    def new_place_template(session: Session, user_id: tp.Union[str, int], place: str):
        user = session.query(User).filter_by(user_id=str(user_id)).first()
        if user.place_templates is None:
            user.place_templates = [place]
        else:
            user.place_templates = [*user.place_templates, place]
        session.commit()

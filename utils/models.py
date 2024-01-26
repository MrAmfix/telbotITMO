from sqlalchemy import Column, Integer, JSON, String, ARRAY, Date
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    def __repr__(self):
        return (f'User(user_id = {self.user_id}, full_name = {self.full_name}, is_check_logs = {self.is_check_logs}, '
                f'templates = {str([str(i) for i in self.templates])},'
                f' place_templates = {str([str(i) for i in self.place_templates])})')

    user_id = Column(String, primary_key=True)
    full_name = Column(String)
    is_check_logs = Column(Integer, default=0)
    templates = Column(JSON)
    place_templates = Column(ARRAY(String))


class Note(Base):
    __tablename__ = 'notes'

    def __repr__(self):
        return (f'Note(note_id = {self.note_id}, time_range = {self.time_range}, student_id = {self.student_id}, '
                f'logs = {str([str(i) for i in self.logs])})')

    note_id = Column(Integer, primary_key=True, autoincrement=True)
    time_range = Column(String)
    student_id = Column(String)
    logs = Column(ARRAY(String))


class TableNote(Base):
    __tablename__ = 'table_notes'

    def __repr__(self):
        return (f'TableNote(table_id = {self.table_id}, creator_id = {self.creator_id}, date = {self.date} '
                f'notes_id = {str([str(i) for i in self.notes_id])})')

    table_id = Column(Integer, primary_key=True, autoincrement=True)
    notes_id = Column(ARRAY(Integer))
    creator_id = Column(String)
    date = Column(Date)


class Dict(Base):
    __tablename__ = 'dict'

    def __repr__(self):
        return f'Dict(dict_key = {self.dict_key}, dict_value = {self.dict_value})'

    dict_key = Column(Integer, primary_key=True, autoincrement=True)
    dict_value = Column(String)


class Log(Base):
    __tablename__ = 'los'

    def __repr__(self):
        return f'Log(log_id = {self.log_id}, log_text = {self.log_text})'

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    log_text = Column(String)

from sqlalchemy import Column, Integer, JSON, String, ARRAY
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    user_id = Column(String, primary_key=True)
    full_name = Column(String)
    is_check_logs = Column(Integer, default=0)
    templates = Column(JSON)


class Note(Base):
    __tablename__ = 'notes'

    note_id = Column(Integer, primary_key=True, autoincrement=True)
    time_range = Column(String)
    student_id = Column(String)
    logs = Column(ARRAY(String))


class TableNote(Base):
    __tablename__ = 'table_notes'

    table_id = Column(Integer, primary_key=True, autoincrement=True)
    notes_id = Column(ARRAY(Integer))
    creator_id = Column(String)


class Dict(Base):
    __tablename__ = 'dict'

    dict_key = Column(Integer, primary_key=True, autoincrement=True)
    dict_value = Column(String)


class Log(Base):
    __tablename__ = 'logs'

    log_text = Column(String)

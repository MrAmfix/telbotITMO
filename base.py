import psycopg2

from config import DB_PORT, DB_HOST, DB_PASS, DB_USER, DB_NAME
from datetime import datetime


connect = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT)
connect.autocommit = True


def logging(text):
    with connect.cursor() as cursor:
        cursor.execute(f"""INSERT INTO logs (log_text) VALUES (\'[{datetime.now()}] : {text}\')""")


def registration(user_id: int, full_name: str):
    with connect.cursor() as cursor:
        cursor.execute(f"""INSERT INTO users (user_id, full_name) VALUES (\'{user_id}\',\'{full_name}\')""")


def update_fullname(user_id: int, full_name: str):
    with connect.cursor() as cursor:
        cursor.execute(f"""UPDATE users SET full_name = \'{full_name}\' WHERE user_id = \'{user_id}\'""")


def is_registered(user_id: int):
    with connect.cursor() as cursor:
        cursor.execute(f"""SELECT full_name FROM users WHERE user_id = \'{user_id}\'""")
        full_name = cursor.fetchone()
        if full_name is not None:
            return full_name
        return False

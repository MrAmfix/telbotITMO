import psycopg2
from config import DB_PORT, DB_HOST, DB_PASS, DB_USER, DB_NAME
import json


connect = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT)
connect.autocommit = True

if __name__ == '__main__':
    with connect.cursor() as cursor:
        cursor.execute(f'''SELECT templates FROM users WHERE user_id = \'1016391777\'''')
        result = cursor.fetchone()
        if result:
            json_data = result[0]
            print(result)
            print(json_data)
            user_dict = json_data
            print(user_dict['Monday'])

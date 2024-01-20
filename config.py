from decouple import config

_CALL = '~|'
FLAGS = ['hr', 'hd', 'mr', 'md']
BOT_TOKEN = config('BOT_TOKEN')
ID_OWNER = config('ID_OWNER')
DB_NAME = config('DB_NAME')
DB_USER = config('DB_USER')
DB_PASS = config('DB_PASS')
DB_HOST = config('DB_HOST')
DB_PORT = config('DB_PORT')
DB_ADAPTER = config('DB_ADAPTER')

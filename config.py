from decouple import config

FLAGS = ['hr', 'hd', 'mr', 'md']
BOT_TOKEN = config('BOT_TOKEN')
ID_OWNER = config('ID_OWNER')
DB_NAME = config('DB_NAME_S')
DB_USER = config('DB_USER_S')
DB_PASS = config('DB_PASS_S')
DB_HOST = config('DB_HOST_S')
DB_PORT = config('DB_PORT_S')

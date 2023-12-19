from aiogram.fsm.state import StatesGroup, State


class States(StatesGroup):
    wait_keyword = State()

    check_log = State()

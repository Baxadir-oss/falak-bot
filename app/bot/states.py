from aiogram.fsm.state import State, StatesGroup


class LocationFlow(StatesGroup):
    waiting_city_name = State()


class SettingsFlow(StatesGroup):
    waiting_notify_hour = State()

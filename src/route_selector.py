from typing import Union

from aiogram import Router
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup
from typing import Literal

from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.models.stations import Station
from src.search.find_station import find_station

route_selector = Router()


class RouteSelectState(StatesGroup):
    from_station_search = State()
    from_station_second_search = State()
    to_station_search = State()
    to_station_second_search = State()


class SelectStationCallback(CallbackData, prefix="select_station"):
    direction: Literal['from'] | Literal['to']
    code: str


def select_stations_keyboard(stations: list[Station],
                             direction: Literal['from'] | Literal['to']) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for index, station in enumerate(stations[:15]):
        builder.button(text=f'🛤 | {station.title} ({station.region})',
                       callback_data=SelectStationCallback(direction=direction, code=station.code))
    builder.adjust(1, repeat=True)
    return builder.as_markup()


@route_selector.callback_query(lambda c: c.data == 'find_route')
async def find_route(c: CallbackQuery, state: FSMContext):
    await state.set_state(RouteSelectState.from_station_search)
    await c.message.reply('🚆🛃 <b>Введите название станции или платформы ОТКУДА вы отправляетесь</b>', parse_mode='HTML')


@route_selector.message(RouteSelectState.from_station_search)
async def from_station_handler(message: Message, state: FSMContext):
    stations = find_station(message.text.casefold())
    if len(stations) == 0:
        await message.reply(f"❌🛃 <b>Станция не найдена. Пожалуйста, укажите корректное название станции.</b>",
                            parse_mode='HTML')
    elif len(stations) == 1:
        await message.reply(
            f'🚆🛃 <b>Найдена станция "{stations[0].title}" в {stations[0].region}. Введите название станции или платформы КУДА вы едете.</b>',
            parse_mode='HTML')
        await state.update_data(from_station=stations[0].code)
        await state.set_state(RouteSelectState.to_station_search)
    else:
        await message.reply(
            f'🚆🛃 <b>Найдены следующие станции с похожим названием:</b>',
            parse_mode='HTML', reply_markup=select_stations_keyboard(stations, direction='from'))
        await state.update_data(stations_list=stations)


@route_selector.message(RouteSelectState.to_station_search)
async def to_station_handler(message: Message, state: FSMContext):
    stations = find_station(message.text.casefold())
    if len(stations) == 0:
        await message.reply(f'❌🛃 <b>Станция не найдена. Пожалуйста, укажите корректное название станции.</b>',
                            parse_mode='HTML')
    elif len(stations) == 1:
        await message.reply(
            f'🚆🛃 <b>Найдена станция "{stations[0].title}" ({stations[0].region}). Маршрут был установлен.</b>',
            parse_mode='HTML')
        await state.update_data(to_station=stations[0].code)
        await state.set_state()

    else:
        await message.reply(
            f'🚆🛃 <b>Найдены следующие станции с похожим названием:</b>',
            parse_mode='HTML', reply_markup=select_stations_keyboard(stations, direction='to'))
        await state.update_data(stations_list=stations)


@route_selector.callback_query(SelectStationCallback.filter())
async def select_station_handler(callback: CallbackQuery, callback_data: SelectStationCallback, state: FSMContext):
    data = await state.get_data()
    stations_list: list[Station] = data['stations_list']
    station: Station = list(filter(lambda s: s.code == callback_data.code, stations_list))[0]
    if callback_data.direction == 'from':
        await callback.message.edit_text(
            f'🚆🛃 <b>Выбрана станция "{station.title}" ({station.region}). Введите название станции или платформы КУДА вы едете.</b>',
            parse_mode='HTML')
        await state.set_state(RouteSelectState.to_station_search)
        await state.update_data(from_station=callback_data.code)
    elif callback_data.direction == 'to':
        await callback.message.edit_text(
            f'🚆🛃 <b>Найдена станция "{station.title}" ({station.region}). Маршрут был установлен.</b>',
            parse_mode='HTML')
        await state.set_state()
        await state.update_data(to_station=callback_data.code)

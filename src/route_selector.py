from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message

from src.models.stations import Station
from src.search.find_station import find_station

route_selector = Router()


class RouteSelectState(StatesGroup):
    from_station_search = State()
    from_station_second_search = State()
    to_station_search = State()
    to_station_second_search = State()


def select_stations_list(stations: list[Station]) -> str:
    resp = []
    for index, station in enumerate(stations[:10]):
        resp.append(f'{index + 1}. {station.title} ({station.region})')
    return '\n'.join(resp)


@route_selector.callback_query(lambda c: c.data == 'find_route')
async def find_route(c: CallbackQuery, state: FSMContext):
    await state.set_state(RouteSelectState.from_station_search)
    await c.message.reply('🚆🛃 <b>Введите название станции или платформы ОТКУДА вы отправляетесь</b>', parse_mode='HTML')


@route_selector.message(RouteSelectState.from_station_search)
async def from_station_handler(message: Message, state: FSMContext):
    stations = find_station(message.text.casefold())
    if len(stations) == 0:
        await message.reply(f"❌🛃 <b>Станция не найдена. Пожалуйста, укажите корректное название станции.</b>", parse_mode='HTML')
    elif len(stations) == 1:
        await message.reply(
            f'🚆🛃 <b>Найдена станция "{stations[0].title}" в {stations[0].region}. Введите название станции или платформы КУДА вы едете.</b>', parse_mode='HTML')
        await state.update_data(from_station=stations[0].code)
        await state.set_state(RouteSelectState.to_station_search)
    else:
        await message.reply(f'🚆🛃 <b>Найдены следующие станции с похожим названием:\n{select_stations_list(stations)}\n\nВведите номер нужной вам станции.</b>', parse_mode='HTML')
        await state.set_state(RouteSelectState.from_station_second_search)
        await state.update_data(stations_list=stations)


@route_selector.message(RouteSelectState.from_station_second_search)
async def from_station_second_search_handler(message: Message, state: FSMContext):
    index = 1
    try:
        index = int(message.text.casefold())
        if index > 10 or index < 1:
            raise Exception
    except:
        return await message.reply('f❌🛃 <b>Неверный номер станции</b>', parse_mode='HTML')
    data = await state.get_data()
    station: Station = data['stations_list'][index - 1]
    await message.reply(
        f'🚆🛃 <b>Выбрана станция "{station.title}" ({station.region}). Введите название станции или платформы КУДА вы едете.</b>', parse_mode='HTML')
    await state.update_data(from_station=station.code)
    await state.set_state(RouteSelectState.to_station_search)


@route_selector.message(RouteSelectState.to_station_search)
async def to_station_handler(message: Message, state: FSMContext):
    stations = find_station(message.text.casefold())
    if len(stations) == 0:
        await message.reply(f'❌🛃 <b>Станция не найдена. Пожалуйста, укажите корректное название станции.</b>', parse_mode='HTML')
    elif len(stations) == 1:
        await message.reply(
            f'🚆🛃 <b>Найдена станция "{stations[0].title}" ({stations[0].region}). Маршрут был установлен.</b>', parse_mode='HTML')
        await state.update_data(to_station=stations[0].code)
        await state.set_state()

    else:
        await message.reply(f'🚆🛃 <b>Найдены следующие станции с похожим названием:\n{select_stations_list(stations)}\n\nВведите номер нужной вам станции.</b>', parse_mode='HTML')
        await state.set_state(RouteSelectState.to_station_second_search)
        await state.update_data(stations_list=stations)


@route_selector.message(RouteSelectState.to_station_second_search)
async def to_station_second_search_handler(message: Message, state: FSMContext):
    index = 1
    try:
        index = int(message.text.casefold())
        if index > 10 or index < 1:
            raise Exception
    except:
        return await message.reply(f'❌🛃 <b>Неверный номер станции</b>', parse_mode='HTML')
    data = await state.get_data()
    station: Station = data['stations_list'][index - 1]
    await message.reply(f'🚆🛃 <b>Найдена станция "{station.title}" ({station.region}). Маршрут был установлен.</b>', parse_mode='HTML')
    await state.update_data(to_station=station.code)
    await state.set_state()

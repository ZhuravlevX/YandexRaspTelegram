import os
from datetime import datetime

from aiogram import Router
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup
from typing import Literal
from pytz import timezone

from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.models.stations import Station
from src.models.cities import City
from src.route_select.find_station import find_station
from src.route_select.find_city import find_city
from src.get_suburban_info import get_suburban_info_route
from src.get_train_info import get_train_info

station_emojis = {
    "train_station": "🏫",
    "station": "🚉",
    "airport": "🛫"
}

route_selector = Router()
token_yandex = os.getenv('TOKEN_YANDEX')


class RouteSelectState(StatesGroup):
    from_station_search = State()
    to_station_search = State()
    from_city_search = State()
    to_city_search = State()


class SelectStationCallback(CallbackData, prefix="select_station"):
    direction: Literal['from', 'to']
    code: str


class SelectCityCallback(CallbackData, prefix="select_city"):
    direction: Literal['from', 'to']
    code: str


async def select_stations_keyboard(stations: list[Station],
                                   direction: Literal['from', 'to'], state: FSMContext) -> InlineKeyboardMarkup:
    stations_list = {}
    builder = InlineKeyboardBuilder()

    for index, station in enumerate(stations[:15]):
        stations_list[station.code] = f'«{station.title}» ({station.region})'
        builder.button(text=f'{station_emojis.get(station.station_type, "🛤")} | {station.title} ({station.region})',
                       callback_data=SelectStationCallback(direction=direction, code=station.code))
    await state.update_data(stations=stations_list)

    builder.adjust(1, repeat=True)
    return builder.as_markup()


async def select_cities_keyboard(cities: list[City],
                                 direction: Literal['from', 'to'], state: FSMContext) -> InlineKeyboardMarkup:
    cities_list = {}
    builder = InlineKeyboardBuilder()
    for index, city in enumerate(cities[:15]):
        cities_list[city.code] = f'«{city.region}»'
        builder.button(text=f'🏙 | «{city.region}»',
                       callback_data=SelectCityCallback(direction=direction, code=city.code))
    await state.update_data(cities=cities_list)
    builder.adjust(1, repeat=True)
    return builder.as_markup()


@route_selector.callback_query(lambda c: c.data == 'find_route')
async def find_route(c: CallbackQuery, state: FSMContext):
    await state.set_state(RouteSelectState.from_station_search)
    await c.message.reply('🏫🔍 <b>Введите название станции или платформы ОТКУДА вы отправляетесь.</b>',
                          parse_mode='HTML')


@route_selector.callback_query(lambda c: c.data == 'find_route_city')
async def find_route_city(c: CallbackQuery, state: FSMContext):
    await state.set_state(RouteSelectState.from_city_search)
    await c.message.reply('🏙🔍 <b>Введите название города ОТКУДА вы отправляетесь.</b>', parse_mode='HTML')


@route_selector.message(RouteSelectState.from_station_search)
async def from_station_handler(message: Message, state: FSMContext):
    stations = find_station(message.text.casefold())

    if len(stations) == 0:
        await message.reply(
            f"❌🔍 <b>Станция или платформа с таким названием не найдена. Пожалуйста, укажите корректное название станции или платформы.</b>",
            parse_mode='HTML')
    elif len(stations) == 1:
        await message.reply(
            f'🏫🔍 <b>Найдена станция «{stations[0].title}» ({stations[0].region}). Введите название станции или платформы КУДА вы едете.</b>',
            parse_mode='HTML')
        await state.update_data(from_station=stations[0].code,
                                from_station_title=f"«{stations[0].title}» ({stations[0].region})")
        await state.set_state(RouteSelectState.to_station_search)
    else:
        await message.reply(
            f'🏫🔍 <b>Найдены следующие станции с похожим названием:</b>',
            parse_mode='HTML', reply_markup=(await select_stations_keyboard(stations, direction='from', state=state)))


@route_selector.message(RouteSelectState.to_station_search)
async def to_station_handler(message: Message, state: FSMContext):
    stations = find_station(message.text.casefold())
    data = await state.get_data()
    tz = timezone(data.get('timezone', 'Europe/Moscow'))
    from_station = data.get('from_station')
    from_station_title = data.get('to_station_title')

    if len(stations) == 0:
        await message.reply(
            f'❌🔍 <b>Станция или платформа с таким названием не найдена. Пожалуйста, укажите корректное название станции или платформы.</b>',
            parse_mode='HTML')
    elif len(stations) == 1:
        await state.update_data(to_station=stations[0].code,
                                to_station_title=f"«{stations[0].title}» ({stations[0].region})")
        suburban_info_check = get_suburban_info(from_station, stations[0].code, str(tz))
        if suburban_info_check:
            await message.reply(
                f'🏫🔍 <b>Найдена станция «{stations[0].title}» ({stations[0].region}). Маршрут следования для расписания пригородных поездов от {from_station_title} по «{stations[0].title}» ({stations[0].region}) был установлен.</b>',
                parse_mode='HTML')
            await state.set_state()
        else:
            await message.reply(
                f'❌🔍 <b>К сожалению при поиске расписания по указанному вашему маршруту следования ничего не было найдено. Пожалуйста введите корректное название станции или платформы на вашем направлении КУДА вам нужно прибыть.</b>',
                parse_mode='HTML')

    else:
        await message.reply(
            f'🏫🔍 <b>Найдены следующие станции с похожим названием:</b>',
            parse_mode='HTML', reply_markup=(await select_stations_keyboard(stations, direction='to', state=state)))


@route_selector.callback_query(SelectStationCallback.filter())
async def select_station_handler(callback: CallbackQuery, callback_data: SelectStationCallback, state: FSMContext):
    data = await state.get_data()
    tz = timezone(data.get('timezone', 'Europe/Moscow'))
    from_station = data.get('from_station')
    from_station_title = data.get('from_station_title')

    stations_list = data['stations']
    station = stations_list[callback_data.code]
    if callback_data.direction == 'from':
        await callback.message.edit_text(
            f'🏫🔍 <b>Выбрана станция {station}. Введите название станции или платформы КУДА вы едете.</b>',
            parse_mode='HTML')
        await state.set_state(RouteSelectState.to_station_search)
        await state.update_data(from_station=callback_data.code, from_station_title=station)
    elif callback_data.direction == 'to':
        await state.update_data(to_station=callback_data.code, to_station_title=station)
        suburban_info_check = get_suburban_info(from_station, callback_data.code, str(tz))
        if suburban_info_check:
            await callback.message.edit_text(
                f'🏫🔍 <b>Найдена станция {station}. Маршрут следования для расписания пригородных поездов от {from_station_title} по {station} был установлен.</b>',
                parse_mode='HTML')
            await state.set_state()
        else:
            await callback.message.edit_text(
                f'❌🔍 <b>К сожалению при поиске расписания по указанному вашему маршруту следования ничего не было найдено. Пожалуйста введите корректное название станции или платформы на вашем направлении КУДА вам нужно прибыть.</b>',
                parse_mode='HTML')


@route_selector.message(RouteSelectState.from_city_search)
async def from_city_handler(message: Message, state: FSMContext):
    cities = find_city(message.text.casefold())

    if len(cities) == 0:
        await message.reply(
            f"❌🔍 <b>Город с таким названием не найден. Пожалуйста, укажите корректное название города.</b>",
            parse_mode='HTML')
    elif len(cities) == 1:
        await message.reply(
            f'🏙🔍 <b>Найден город «{cities[0].region}». Введите название города КУДА вы едете.</b>',
            parse_mode='HTML')
        await state.update_data(from_city=cities[0].code, from_city_title=f"«{cities[0].region}»")
        await state.set_state(RouteSelectState.to_city_search)
    else:
        await message.reply(
            f'🏙🔍 <b>Найдены следующие города с похожим названием:</b>',
            parse_mode='HTML', reply_markup=(await select_cities_keyboard(cities, direction='from', state=state)))


@route_selector.message(RouteSelectState.to_city_search)
async def to_city_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    from_city_title = data.get('from_city_title')
    cities = find_city(message.text.casefold())
    tz = timezone(data.get('timezone', 'Europe/Moscow'))

    from_city = data.get('from_city')

    if len(cities) == 0:
        await message.reply(
            f"❌🔍 <b>Город с таким названием не найден. Пожалуйста, укажите корректное название города.</b>",
            parse_mode='HTML')
    elif len(cities) == 1:
        await state.update_data(to_city=cities[0].code, to_city_title=f"«{cities[0].region}»")
        train_info_check = get_train_info(from_city, cities[0].code, str(tz))
        if train_info_check:
            await message.reply(
                f'🏙🔍 <b>Найден город «{cities[0].region}». Маршрут следования для расписания поездов дальнего следования от {from_city_title} до «{cities[0].region}» был установлен.</b>',
                parse_mode='HTML')
            await state.set_state()
        else:
            await message.reply(
                f'❌🔍 <b>К сожалению при поиске расписания по указанному вашему маршруту следования ничего не было найдено. Пожалуйста введите корректное название города к которым имеется возможность доехать.</b>',
                parse_mode='HTML')
    else:
        await message.reply(
            f'🏙🔍 <b>Найдены следующие города с похожим названием:</b>',
            parse_mode='HTML', reply_markup=(await select_cities_keyboard(cities, direction='to', state=state)))


@route_selector.callback_query(SelectCityCallback.filter())
async def select_city_handler(callback: CallbackQuery, callback_data: SelectCityCallback, state: FSMContext):
    data = await state.get_data()
    from_city = data.get('from_city')
    from_city_title = data.get('from_city_title')
    tz = timezone(data.get('timezone', 'Europe/Moscow'))

    cities_list = data['cities']
    city = cities_list[callback_data.code]
    if callback_data.direction == 'from':
        await callback.message.edit_text(
            f'🏙🔍 <b>Выбран город {city}. Введите название города КУДА вы едете.</b>',
            parse_mode='HTML')
        await state.set_state(RouteSelectState.to_city_search)
        await state.update_data(from_city=callback_data.code, from_city_title=f"«{callback_data.region}»")
    elif callback_data.direction == 'to':
        await state.update_data(to_city=callback_data.code, to_city_title=f"«{callback_data.region}»")
        train_info_check = get_train_info(from_city, callback_data.code, str(tz))
        if train_info_check:
            await callback.message.edit_text(
                f'🏙🔍 <b>Найден город {city}. Маршрут следования для расписания поездов дальнего следования от {from_city_title} до {city} был установлен.</b>',
                parse_mode='HTML')
            await state.set_state()
        else:
            await callback.message.edit_text(
                f'❌🔍 <b>К сожалению при поиске расписания по указанному вашему маршруту следования ничего не было найдено. Пожалуйста введите корректное название города к которым имеется возможность доехать.</b>',
                parse_mode='HTML')

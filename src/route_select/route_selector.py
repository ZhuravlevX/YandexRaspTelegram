import os
import requests
from datetime import datetime, timedelta

from aiogram import Router
from aiogram.filters.command import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup
from typing import Literal

from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.models.stations import Station
from src.route_select.find_station import find_station
from src.get_train_info import get_train_info

route_selector = Router()
token_yandex = os.getenv('TOKEN_YANDEX')


class RouteSelectState(StatesGroup):
    from_station_search = State()
    to_station_search = State()


class SelectStationCallback(CallbackData, prefix="select_station"):
    direction: Literal['from', 'to']
    code: str


async def select_stations_keyboard(stations: list[Station],
                                   direction: Literal['from', 'to'], state: FSMContext) -> InlineKeyboardMarkup:
    stations_list = {}
    builder = InlineKeyboardBuilder()
    for index, station in enumerate(stations[:15]):
        stations_list[station.code] = f'«{station.title}» ({station.region})'
        if station.station_type == "train_station":
            builder.button(text=f'🏫 | {station.title} ({station.region})',
                           callback_data=SelectStationCallback(direction=direction, code=station.code))
        elif station.station_type == "station":
            builder.button(text=f'🚉 | {station.title} ({station.region})',
                           callback_data=SelectStationCallback(direction=direction, code=station.code))
        else:
            builder.button(text=f'🛤 | {station.title} ({station.region})',
                           callback_data=SelectStationCallback(direction=direction, code=station.code))
    await state.update_data(stations=stations_list)
    builder.adjust(1, repeat=True)
    return builder.as_markup()


@route_selector.callback_query(lambda c: c.data == 'find_route')
async def find_route(c: CallbackQuery, state: FSMContext):
    await state.set_state(RouteSelectState.from_station_search)
    await c.message.reply('🚆🛃 <b>Введите название станции или платформы ОТКУДА вы отправляетесь</b>', parse_mode='HTML')


@route_selector.message(Command('route'))
async def find_route(message: Message, state: FSMContext):
    await state.set_state(RouteSelectState.from_station_search)
    await message.reply('🚆🛃 <b>Введите название станции или платформы ОТКУДА вы отправляетесь</b>', parse_mode='HTML')


@route_selector.message(RouteSelectState.from_station_search)
async def from_station_handler(message: Message, state: FSMContext):
    stations = find_station(message.text.casefold())

    if len(stations) == 0:
        await message.reply(
            f"❌🛃 <b>Станция или платформа с таким названием не найдена. Пожалуйста, укажите корректное название станции или платформы.</b>",
            parse_mode='HTML')
    elif len(stations) == 1:
        await message.reply(
            f'🚆🛃 <b>Найдена станция «{stations[0].title}» ({stations[0].region}). Введите название станции или платформы КУДА вы едете.</b>',
            parse_mode='HTML')
        await state.update_data(from_station=stations[0].code)
        await state.set_state(RouteSelectState.to_station_search)
    else:
        await message.reply(
            f'🚆🛃 <b>Найдены следующие станции с похожим названием:</b>',
            parse_mode='HTML', reply_markup=(await select_stations_keyboard(stations, direction='from', state=state)))


@route_selector.message(RouteSelectState.to_station_search)
async def to_station_handler(message: Message, state: FSMContext):
    stations = find_station(message.text.casefold())

    data = await state.get_data()

    from_station = data.get('from_station')

    if len(stations) == 0:
        await message.reply(
            f'❌🛃 <b>Станция или платформа с таким названием не найдена. Пожалуйста, укажите корректное название станции или платформы.</b>',
            parse_mode='HTML')
    elif len(stations) == 1:
        await state.update_data(to_station=stations[0].code)
        train_info_check = get_train_info(from_station, stations[0].code)
        if train_info_check:
            await message.reply(
                f'🚆🛃 <b>Найдена станция «{stations[0].title}» ({stations[0].region}). Маршрут следования для расписания был установлен.</b>',
                parse_mode='HTML')
            await state.set_state()
        else:
            await message.reply(
                f'❌🛃 <b>К сожалению при поиске расписания по указанному вашему маршруту следования ничего не было найдено. Пожалуйста введите корректное название станции или платформы на вашем направлении КУДА вам нужно прибыть.</b>',
                parse_mode='HTML')

    else:
        await message.reply(
            f'🚆🛃 <b>Найдены следующие станции с похожим названием:</b>',
            parse_mode='HTML', reply_markup=(await select_stations_keyboard(stations, direction='to', state=state)))


@route_selector.callback_query(SelectStationCallback.filter())
async def select_station_handler(callback: CallbackQuery, callback_data: SelectStationCallback, state: FSMContext):
    data = await state.get_data()
    from_station = data.get('from_station')

    stations_list = data['stations']
    station = stations_list[callback_data.code]
    if callback_data.direction == 'from':
        await callback.message.edit_text(
            f'🚆🛃 <b>Выбрана станция {station}. Введите название станции или платформы КУДА вы едете.</b>',
            parse_mode='HTML')
        await state.set_state(RouteSelectState.to_station_search)
        await state.update_data(from_station=callback_data.code)
    elif callback_data.direction == 'to':
        await state.update_data(to_station=callback_data.code)
        train_info_check = get_train_info(from_station, callback_data.code)
        if train_info_check:
            await callback.message.edit_text(
                f'🚆🛃 <b>Найдена станция {station}. Маршрут следования для расписания был установлен.</b>',
                parse_mode='HTML')
            await state.set_state()
        else:
            await callback.message.edit_text(
                f'❌🛃 <b>К сожалению при поиске расписания по указанному вашему маршруту следования ничего не было найдено. Пожалуйста введите корректное название станции или платформы на вашем направлении КУДА вам нужно прибыть.</b>',
                parse_mode='HTML')

import asyncio
from typing import Literal

import requests
from aiogram import Router
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.metro.build_route import build_route_message
from src.models.metro_api import SearchResponse, StationMini, RouterResponse


class MetroRouteSelectState(StatesGroup):
    from_station_search = State()
    to_station_search = State()


class SelectStationCallback(CallbackData, prefix="metro_select_station"):
    direction: Literal['from', 'to']
    id: int


metro_route = Router()


# temp
# TODO: переместить куда-нибудь куда надо
@metro_route.message(Command('metr'))
async def rt(message: Message, state: FSMContext):
    data = await state.get_data()
    if not data['metro_from'] or not data['metro_to']:
        return
    res = requests.get(f'http://127.0.0.1:8080/route?from={data["metro_from"]}&to={data["metro_to"]}')

    if not res.ok:
        return

    route = RouterResponse(**res.json())

    text = build_route_message(route)
    message = await message.reply(text)
    for i in range(360):
        await asyncio.sleep(10)
        new_text = build_route_message(route)
        if new_text != text:
            text = new_text
            await message.edit_text(text)


async def select_stations_keyboard(stations: list[StationMini],
                                   direction: Literal['from', 'to']) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for station in stations:
        builder.button(text=f'{station.name} ({station.lineName})',
                       callback_data=SelectStationCallback(direction=direction, id=station.id))

    builder.adjust(1, repeat=True)
    return builder.as_markup()


async def select_station(station_id, direction, message: Message, state: FSMContext):
    station = StationMini(**requests.get(f'http://127.0.0.1:8080/station/mini/{station_id}').json())
    await state.update_data({f'metro_{direction}': station_id})
    await message.bot.send_message(message.chat.id, f'Выбрана станция {station.name} ({station.lineName})')
    await state.set_state(MetroRouteSelectState.to_station_search if direction == 'from' else None)
    if direction == 'from':
        await message.bot.send_message(message.chat.id, '🏫🔍 <b>Введите название станции КУДА вы отправляетесь.</b>')
    else:
        await message.bot.send_message(message.chat.id, '<b>Выбраны станции</b>')


@metro_route.callback_query(lambda c: c.data == 'metro_find_route')
async def find_route(c: CallbackQuery, state: FSMContext):
    await state.set_state(MetroRouteSelectState.from_station_search)
    await c.message.edit_text('🏫🔍 <b>Введите название станции ОТКУДА вы отправляетесь.</b>')


@metro_route.callback_query(SelectStationCallback.filter())
async def select_station_callback(c: CallbackQuery, callback_data: SelectStationCallback, state: FSMContext):
    await select_station(callback_data.id, callback_data.direction, c.message, state)


@metro_route.message(MetroRouteSelectState.from_station_search)
async def select_from_station(message: Message, state: FSMContext):
    search_res = requests.get(f'http://127.0.0.1:8080/station/search?q={message.text}')

    if not search_res.ok:
        return message.reply('Такой станции не найдено')

    response = SearchResponse(**search_res.json())
    stations = response.stations

    if response.count == 1:
        return await select_station(stations[0].id, 'from', message, state)
    else:
        return await message.bot.send_message(message.chat.id, f'Найдено {response.count} станций. Выберите нужную',
                                              reply_markup=await select_stations_keyboard(stations, 'from'))


@metro_route.message(MetroRouteSelectState.to_station_search)
async def select_to_station(message: Message, state: FSMContext):
    search_res = requests.get(f'http://127.0.0.1:8080/station/search?q={message.text}')

    if not search_res.ok:
        return message.reply('Такой станции не найдено')

    response = SearchResponse(**search_res.json())
    stations = response.stations

    if len(stations) == 1:
        return await select_station(stations[0].id, 'to', message, state)
    else:
        return await message.bot.send_message(message.chat.id, f'Найдено {response.count} станций. Выберите нужную',
                                       reply_markup=await select_stations_keyboard(stations, 'to'))

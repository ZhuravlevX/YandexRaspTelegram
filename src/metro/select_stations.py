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

from src.get_underground_info import get_underground_info, build_route_message
from src.models.metro_api import SearchResponse, StationMini, RouterResponse


line_emojis = {
    "Сокольническая линия": "🔴",
    "Замоскворецкая линия": "🟢",
    "Арбатско-Покровская линия": "🔵",
    "Филёвская линия": "🩵",
    "Кольцевая линия": "🟤",
    "Калужско-Рижская линия": "🟠",
    "Таганско-Краснопресненская линия": "🟣",
    "Калининская линия": "🟡",
    "Серпуховско-Тимирязевская линия": "🤍",
    "Люблинско-Дмитровская линия": "🥗",
    "Бутовская линия": "🏵",
    "Солнцевская линия": "☀",
    "Некрасовская линия": "🌺",
    "Троицкая линия": "🍀",
    "Большая кольцевая линия": "🔄"
}

class MetroRouteSelectState(StatesGroup):
    from_station_search = State()
    to_station_search = State()


class SelectStationCallback(CallbackData, prefix="metro_select_station"):
    direction: Literal['from', 'to']
    id: int


metro_route = Router()


# temp
# TODO: переместить куда-нибудь куда надо

async def select_stations_keyboard(stations: list[StationMini],
                                   direction: Literal['from', 'to']) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for station in stations:
        builder.button(text=f'{line_emojis.get(station.lineName, "🚈")} | {station.name} ({station.lineName})',
                       callback_data=SelectStationCallback(direction=direction, id=station.id))

    builder.adjust(1, repeat=True)
    return builder.as_markup()


async def select_station(station_id, direction, message: Message, state: FSMContext):
    station = StationMini(**requests.get(f'http://127.0.0.1:8080/station/mini/{station_id}').json())
    await state.update_data({f'{direction}_station_underground': station_id})
    await state.set_state(MetroRouteSelectState.to_station_search if direction == 'from' else None)
    if direction == 'from':
        await message.bot.send_message(message.chat.id, f'🚇🔍 <b>Выбрана станция {station.name} ({station.lineName}). Введите название станции КУДА вы отправляетесь.</b>')
    else:
        await message.bot.send_message(message.chat.id, '<b>Выбраны станции</b>')


@metro_route.callback_query(lambda c: c.data == 'metro_find_route')
async def find_route(c: CallbackQuery, state: FSMContext):
    await state.set_state(MetroRouteSelectState.from_station_search)
    await c.message.edit_text('🚇🔍 <b>Введите название станции ОТКУДА вы отправляетесь.</b>')


@metro_route.callback_query(SelectStationCallback.filter())
async def select_station_callback(c: CallbackQuery, callback_data: SelectStationCallback, state: FSMContext):
    await select_station(callback_data.id, callback_data.direction, c.message, state)


@metro_route.message(MetroRouteSelectState.from_station_search)
async def select_from_station(message: Message, state: FSMContext):
    search_res = requests.get(f'http://127.0.0.1:8080/station/search?q={message.text}')

    if not search_res.ok:
        return message.reply('❌🔍 <b>Станция с таким названием не найдена. Пожалуйста, укажите корректное название станции. Если вы указали корректное название, обратитесь к нам через /feedback.</b>')

    response = SearchResponse(**search_res.json())
    stations = response.stations

    if response.count == 1:
        return await select_station(stations[0].id, 'from', message, state)
    else:
        return await message.bot.send_message(message.chat.id, f'🚇🔍 <b>Найдены следующие станции с похожим названием:</b>',
                                              reply_markup=await select_stations_keyboard(stations, 'from'))


@metro_route.message(MetroRouteSelectState.to_station_search)
async def select_to_station(message: Message, state: FSMContext):
    search_res = requests.get(f'http://127.0.0.1:8080/station/search?q={message.text}')

    if not search_res.ok:
        return message.reply('❌🔍 <b>Станция с таким названием не найдена. Пожалуйста, укажите корректное название станции. Если вы указали корректное название, обратитесь к нам через /feedback.</b>')

    response = SearchResponse(**search_res.json())
    stations = response.stations

    if len(stations) == 1:
        return await select_station(stations[0].id, 'to', message, state)
    else:
        return await message.bot.send_message(message.chat.id, f'🚇🔍 <b>Найдены следующие станции с похожим названием:</b>',
                                       reply_markup=await select_stations_keyboard(stations, 'to'))

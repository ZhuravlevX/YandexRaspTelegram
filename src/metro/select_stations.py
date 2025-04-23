import asyncio
from typing import Literal

import requests
from aiogram import Router
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
    "Люблинско-Дмитровская линия": "🥒",
    "Бутовская линия": "🏵",
    "Солнцевская линия": "☀",
    "Некрасовская линия": "🌺",
    "Троицкая линия": "🍀",
    "Большая кольцевая линия": "🔄"
}


class MetroRouteSelectState(StatesGroup):
    from_station_underground = State()
    to_station_underground = State()


class SelectStationCallback(CallbackData, prefix="metro_select_station"):
    direction: Literal['from', 'to']
    id: int


metro_route = Router()


async def delete_previous_messages_except_last(messages: list, bot, last_message_id: int):
    for message in messages:
        if message['message_id'] == last_message_id:
            continue
        try:
            await bot.delete_message(chat_id=message['chat_id'], message_id=message['message_id'])
        except Exception as e:
            print(f"Failed to delete message {message['message_id']}: {e}")


async def select_stations_keyboard(stations: list[StationMini],
                                   direction: Literal['from', 'to']) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for station in stations:
        builder.button(text=f'{line_emojis.get(station.lineName, "🚈")} | «{station.name}»  ({station.lineName})',
                       callback_data=SelectStationCallback(direction=direction, id=station.id))

    builder.adjust(1, repeat=True)
    return builder.as_markup()


async def select_station(station_id, direction, message: Message, state: FSMContext):
    station = StationMini(**requests.get(f'http://127.0.0.1:8080/station/mini/{station_id}').json())
    data = await state.get_data()

    if direction == "to" and station_id == data.get("from_station_underground"):
        await message.reply(
            "❌🔍 <b>Конечная станция не может совпадать со станцией отправления. Невозможно проложить путь. Выберите другую станцию.</b>")
        return
    if direction == "from" and station_id == data.get("to_station_underground"):
        await message.reply(
            "❌🔍 <b>Станция отправления не может совпадать с конечной станцией. Невозможно проложить путь. Выберите другую станцию.</b>")
        return

    await state.update_data({f'{direction}_station_underground': station_id})
    await state.set_state(MetroRouteSelectState.to_station_underground if direction == 'from' else None)

    if direction == 'from':
        await message.bot.send_message(message.chat.id,
                                       f'🚇🔍 <b>Выбрана станция «{station.name}» ({station.lineName}). Введите название станции КУДА вы отправляетесь.</b>')
    else:
        await message.bot.send_message(message.chat.id,
                                       f'🚇🔍 <b>Выбрана станция «{station.name}» ({station.lineName}). Маршрут следования для построения пути установлен.</b>')


@metro_route.callback_query(lambda c: c.data == 'find_underground_route')
async def find_route(c: CallbackQuery, state: FSMContext):
    await state.set_state(MetroRouteSelectState.from_station_underground)
    response = await c.message.edit_text('🚇🔍 <b>Введите название станции ОТКУДА вы отправляетесь.</b>')
    data = await state.get_data()
    messages = data.get('messages', [])
    messages.append({'chat_id': response.chat.id, 'message_id': response.message_id})
    await state.update_data(messages=messages)


@metro_route.message(MetroRouteSelectState.from_station_underground)
async def select_from_station(message: Message, state: FSMContext):
    search_res = requests.get(f'http://127.0.0.1:8080/station/search?q={message.text}')
    data = await state.get_data()

    messages = data.get('messages', [])
    messages.append({'chat_id': message.chat.id, 'message_id': message.message_id})
    await state.update_data(messages=messages)

    if not search_res.ok:
        response = await message.reply(
            '❌🔍 <b>Станция с таким названием не найдена. Пожалуйста, укажите корректное название станции.</b>')
        messages.append({'chat_id': response.chat.id, 'message_id': response.message_id})
        await state.update_data(messages=messages)
        return

    response_data = SearchResponse(**search_res.json())
    stations = response_data.stations

    if response_data.count == 1:
        await select_station(stations[0].id, 'from', message, state)
    else:
        response = await message.bot.send_message(
            message.chat.id,
            f'🚇🔍 <b>Найдены следующие станции с похожим названием:</b>',
            reply_markup=await select_stations_keyboard(stations, 'from')
        )
        messages.append({'chat_id': response.chat.id, 'message_id': response.message_id})
        await state.update_data(messages=messages)


@metro_route.message(MetroRouteSelectState.to_station_underground)
async def select_to_station(message: Message, state: FSMContext):
    search_res = requests.get(f'http://127.0.0.1:8080/station/search?q={message.text}')
    data = await state.get_data()

    messages = data.get('messages', [])
    messages.append({'chat_id': message.chat.id, 'message_id': message.message_id})
    await state.update_data(messages=messages)

    if not search_res.ok:
        response = await message.reply(
            '❌🔍 <b>Станция с таким названием не найдена. Пожалуйста, укажите корректное название станции.</b>')
        messages.append({'chat_id': response.chat.id, 'message_id': response.message_id})
        await state.update_data(messages=messages)
        return

    response_data = SearchResponse(**search_res.json())
    stations = response_data.stations

    if len(stations) == 1:
        await select_station(stations[0].id, 'to', message, state)
    else:
        response = await message.bot.send_message(
            message.chat.id,
            f'🚇🔍 <b>Найдены следующие станции с похожим названием:</b>',
            reply_markup=await select_stations_keyboard(stations, 'to')
        )
        messages.append({'chat_id': response.chat.id, 'message_id': response.message_id})
        await state.update_data(messages=messages)

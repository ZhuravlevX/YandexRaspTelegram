import os

from aiogram import Router
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from typing import Literal
from pytz import timezone
import requests

from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.models.stations import Station
from src.models.cities import City
from src.route_select.find_station import find_station
from src.route_select.find_city import find_city
from src.get_suburban_info import get_suburban_info
from src.get_train_info import get_train_info
from src.models.metro_api import SearchResponse, StationMini

station_emojis = {
    "train_station": "🏫",
    "station": "🚉",
    "airport": "🛫"
}

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

route_selector = Router()
token_yandex = os.getenv('TOKEN_YANDEX')


class RouteSelectState(StatesGroup):
    from_station_search = State()
    to_station_search = State()
    from_city_search = State()
    to_city_search = State()
    from_station_underground = State()
    to_station_underground = State()


class SelectStationCallback(CallbackData, prefix="select_station"):
    direction: Literal['from', 'to']
    code: str


class SelectCityCallback(CallbackData, prefix="select_city"):
    direction: Literal['from', 'to']
    code: str


class SelectUndergroundCallback(CallbackData, prefix="select_underground"):
    direction: Literal['from', 'to']
    id: int


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
    response = await c.message.edit_text('🏫🔍 <b>Введите название станции или платформы ОТКУДА вы отправляетесь.</b>',
                                         parse_mode='HTML')
    data = await state.get_data()
    messages = data.get('messages', [])
    messages.append({'chat_id': response.chat.id, 'message_id': response.message_id})
    await state.update_data(messages=messages)


@route_selector.callback_query(lambda c: c.data == 'find_route_city')
async def find_route_city(c: CallbackQuery, state: FSMContext):
    await state.set_state(RouteSelectState.from_city_search)
    response = await c.message.edit_text('🏙🔍 <b>Введите название города ОТКУДА вы отправляетесь.</b>',
                                         parse_mode='HTML')
    data = await state.get_data()
    messages = data.get('messages', [])
    messages.append({'chat_id': response.chat.id, 'message_id': response.message_id})
    await state.update_data(messages=messages)


async def delete_previous_messages(messages: list, bot, last_message_id: int, state: FSMContext):
    for message_id in messages:
        if message_id['message_id'] == last_message_id:
            continue
        try:
            await bot.delete_message(chat_id=message_id['chat_id'], message_id=message_id['message_id'])
        except Exception as e:
            print(f"Failed to delete message {message_id['message_id']}: {e}")
    await state.update_data(messages=[])


@route_selector.message(RouteSelectState.from_station_search)
async def from_station_handler(message: Message, state: FSMContext):
    stations = find_station(message.text.casefold())
    data = await state.get_data()

    messages = data.get('messages', [])
    messages.append({'chat_id': message.chat.id, 'message_id': message.message_id})
    await state.update_data(messages=messages)

    if len(stations) == 0:
        response = await message.reply(
            f"❌🔍 <b>Станция или платформа с таким названием не найдена. Пожалуйста, укажите корректное название станции.</b>",
            parse_mode='HTML')
        messages.append({'chat_id': response.chat.id, 'message_id': response.message_id})
        await state.update_data(messages=messages)
    elif len(stations) == 1:
        response = await message.reply(
            f'🏫🔍 <b>Найдена станция «{stations[0].title}» ({stations[0].region}). Введите название станции или платформы КУДА вы едете.</b>',
            parse_mode='HTML')
        messages.append({'chat_id': response.chat.id, 'message_id': response.message_id})
        await state.update_data(messages=messages)
        await state.update_data(from_station=stations[0].code,
                                from_station_title=f"«{stations[0].title}» ({stations[0].region})")
        await state.set_state(RouteSelectState.to_station_search)
    else:
        response = await message.reply(
            f'🏫🔍 <b>Найдены следующие станции с похожим названием:</b>',
            parse_mode='HTML', reply_markup=(await select_stations_keyboard(stations, direction='from', state=state)))
        messages.append({'chat_id': response.chat.id, 'message_id': response.message_id})
        await state.update_data(messages=messages)


@route_selector.message(RouteSelectState.to_station_search)
async def to_station_handler(message: Message, state: FSMContext):
    stations = find_station(message.text.casefold())
    data = await state.get_data()
    tz = timezone(data.get('timezone', 'Europe/Moscow'))
    from_station = data.get('from_station')
    from_station_title = data.get('to_station_title')

    # Save message ID
    messages = data.get('messages', [])
    messages.append({'chat_id': message.chat.id, 'message_id': message.message_id})
    await state.update_data(messages=messages)

    if len(stations) == 0:
        response = await message.reply(
            f'❌🔍 <b>Станция или платформа с таким названием не найдена. Пожалуйста, укажите корректное название станции.</b>',
            parse_mode='HTML')
        messages.append({'chat_id': response.chat.id, 'message_id': response.message_id})
        await state.update_data(messages=messages)
    elif len(stations) == 1:
        await state.update_data(to_station=stations[0].code,
                                to_station_title=f"«{stations[0].title}» ({stations[0].region})")
        suburban_info_check = get_suburban_info(from_station, stations[0].code, str(tz))
        if suburban_info_check:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="↕ | Поиск по маршруту следования", callback_data="send_suburban")]
                ]
            )

            response = await message.reply(
                f'🏫🔍 <b>Найдена станция «{stations[0].title}». Маршрут следования для расписания пригородных поездов от {from_station_title} по {stations[0].title} был установлен.</b>',
                parse_mode='HTML', reply_markup=keyboard
            )
            messages.append({'chat_id': response.chat.id, 'message_id': response.message_id})
            await state.update_data(messages=messages)
            await delete_previous_messages(messages, message.bot, response.message_id, state)
            await state.set_state()
        else:
            response = await message.reply(
                f'❌🔍 <b>К сожалению при поиске расписания по указанному вашему маршруту следования ничего не было найдено.</b>',
                parse_mode='HTML')
            messages.append({'chat_id': response.chat.id, 'message_id': response.message_id})
            await state.update_data(messages=messages)
    else:
        response = await message.reply(
            f'🏫🔍 <b>Найдены следующие станции с похожим названием:</b>',
            parse_mode='HTML', reply_markup=(await select_stations_keyboard(stations, direction='to', state=state)))
        messages.append({'chat_id': response.chat.id, 'message_id': response.message_id})
        await state.update_data(messages=messages)


@route_selector.callback_query(SelectStationCallback.filter())
async def select_station_handler(callback: CallbackQuery, callback_data: SelectStationCallback, state: FSMContext):
    data = await state.get_data()
    tz = timezone(data.get('timezone', 'Europe/Moscow'))
    from_station = data.get('from_station')
    from_station_title = data.get('from_station_title')

    stations_list = data['stations']
    station = stations_list[callback_data.code]
    messages = data.get('messages', [])

    if callback_data.direction == 'from':
        response = await callback.message.edit_text(
            f'🏫🔍 <b>Выбрана станция {station}. Введите название станции или платформы КУДА вы едете.</b>',
            parse_mode='HTML')
        messages.append({'chat_id': response.chat.id, 'message_id': response.message_id})
        await state.update_data(messages=messages)
        await state.set_state(RouteSelectState.to_station_search)
        await state.update_data(from_station=callback_data.code, from_station_title=station)
    elif callback_data.direction == 'to':
        await state.update_data(to_station=callback_data.code, to_station_title=station)
        suburban_info_check = get_suburban_info(from_station, callback_data.code, str(tz))
        if suburban_info_check:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="↕ | Поиск по маршруту следования", callback_data="send_suburban")]
                ]
            )

            response = await callback.message.edit_text(
                f'🏫🔍 <b>Найдена станция {station}. Маршрут следования для расписания пригородных поездов от {from_station_title} по {station} был установлен.</b>',
                parse_mode='HTML', reply_markup=keyboard
            )
            messages.append({'chat_id': response.chat.id, 'message_id': response.message_id})
            await state.update_data(messages=messages)
            await delete_previous_messages(messages, callback.bot, response.message_id, state)
            await state.set_state()
        else:
            response = await callback.message.edit_text(
                f'❌🔍 <b>К сожалению при поиске расписания по указанному вашему маршруту следования ничего не было найдено.</b>',
                parse_mode='HTML')
            messages.append({'chat_id': response.chat.id, 'message_id': response.message_id})
            await state.update_data(messages=messages)


@route_selector.message(RouteSelectState.from_city_search)
async def from_city_handler(message: Message, state: FSMContext):
    cities = find_city(message.text.casefold())
    data = await state.get_data()

    messages = data.get('messages', [])
    messages.append({'chat_id': message.chat.id, 'message_id': message.message_id})
    await state.update_data(messages=messages)

    if len(cities) == 0:
        response = await message.reply(
            f"❌🔍 <b>Город с таким названием не найден. Пожалуйста, укажите корректное название города.</b>",
            parse_mode='HTML')
        messages.append({'chat_id': response.chat.id, 'message_id': response.message_id})
        await state.update_data(messages=messages)
    elif len(cities) == 1:
        response = await message.reply(
            f'🏙🔍 <b>Найден город «{cities[0].region}». Введите название города КУДА вы едете.</b>',
            parse_mode='HTML')
        messages.append({'chat_id': response.chat.id, 'message_id': response.message_id})
        await state.update_data(messages=messages)
        await state.update_data(from_city=cities[0].code, from_city_title=f"«{cities[0].region}»")
        await state.set_state(RouteSelectState.to_city_search)
    else:
        response = await message.reply(
            f'🏙🔍 <b>Найдены следующие города с похожим названием:</b>',
            parse_mode='HTML', reply_markup=(await select_cities_keyboard(cities, direction='from', state=state)))
        messages.append({'chat_id': response.chat.id, 'message_id': response.message_id})
        await state.update_data(messages=messages)


@route_selector.message(RouteSelectState.to_city_search)
async def to_city_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    from_city_title = data.get('from_city_title')
    cities = find_city(message.text.casefold())
    tz = timezone(data.get('timezone', 'Europe/Moscow'))

    from_city = data.get('from_city')

    messages = data.get('messages', [])
    messages.append({'chat_id': message.chat.id, 'message_id': message.message_id})
    await state.update_data(messages=messages)

    if len(cities) == 0:
        response = await message.reply(
            f"❌🔍 <b>Город с таким названием не найден. Пожалуйста, укажите корректное название города.</b>",
            parse_mode='HTML')
        messages.append({'chat_id': response.chat.id, 'message_id': response.message_id})
        await state.update_data(messages=messages)
    elif len(cities) == 1:
        await state.update_data(to_city=cities[0].code, to_city_title=f"«{cities[0].region}»")
        train_info_check = get_train_info(from_city, cities[0].code, str(tz))
        if train_info_check:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="↕ | Поиск по маршруту следования", callback_data="send_train")]
                ]
            )

            response = await message.reply(
                f'🏙🔍 <b>Найден город «{cities[0].region}». Маршрут следования для расписания поездов дальнего следования от {from_city_title} до «{cities[0].region}» был установлен.</b>',
                parse_mode='HTML', reply_markup=keyboard
            )
            messages.append({'chat_id': response.chat.id, 'message_id': response.message_id})
            await state.update_data(messages=messages)
            await delete_previous_messages(messages, message.bot, response.message_id, state)
            await state.set_state()
        else:
            response = await message.reply(
                f'❌🔍 <b>К сожалению при поиске расписания по указанному вашему маршруту следования ничего не было найдено. Пожалуйста введите корректное название города к которым имеется возможность доехать.</b>',
                parse_mode='HTML')
            messages.append({'chat_id': response.chat.id, 'message_id': response.message_id})
            await state.update_data(messages=messages)
    else:
        response = await message.reply(
            f'🏙🔍 <b>Найдены следующие города с похожим названием:</b>',
            parse_mode='HTML', reply_markup=(await select_cities_keyboard(cities, direction='to', state=state)))
        messages.append({'chat_id': response.chat.id, 'message_id': response.message_id})
        await state.update_data(messages=messages)


@route_selector.callback_query(SelectCityCallback.filter())
async def select_city_handler(callback: CallbackQuery, callback_data: SelectCityCallback, state: FSMContext):
    data = await state.get_data()
    from_city = data.get('from_city')
    from_city_title = data.get('from_city_title')
    tz = timezone(data.get('timezone', 'Europe/Moscow'))

    cities_list = data['cities']
    city = cities_list[callback_data.code]
    messages = data.get('messages', [])

    if callback_data.direction == 'from':
        response = await callback.message.edit_text(
            f'🏙🔍 <b>Выбран город {city}. Введите название города КУДА вы едете.</b>',
            parse_mode='HTML')
        messages.append({'chat_id': response.chat.id, 'message_id': response.message_id})
        await state.update_data(messages=messages)
        await state.set_state(RouteSelectState.to_city_search)
        await state.update_data(from_city=callback_data.code, from_city_title=f"«{callback_data.region}»")
    elif callback_data.direction == 'to':
        await state.update_data(to_city=callback_data.code, to_city_title=f"«{callback_data.region}»")
        train_info_check = get_train_info(from_city, callback_data.code, str(tz))
        if train_info_check:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="↕ | Поиск по маршруту следования", callback_data="send_train")]
                ]
            )

            response = await callback.message.edit_text(
                f'🏙🔍 <b>Найден город {city}. Маршрут следования для расписания поездов дальнего следования от {from_city_title} до {city} был установлен.</b>',
                parse_mode='HTML', reply_markup=keyboard
            )
            messages.append({'chat_id': response.chat.id, 'message_id': response.message_id})
            await state.update_data(messages=messages)
            await delete_previous_messages(messages, callback.bot, response.message_id, state)
            await state.set_state()
        else:
            response = await callback.message.edit_text(
                f'❌🔍 <b>К сожалению при поиске расписания по указанному вашему маршруту следования ничего не было найдено. Пожалуйста введите корректное название города к которым имеется возможность доехать.</b>',
                parse_mode='HTML')
            messages.append({'chat_id': response.chat.id, 'message_id': response.message_id})
            await state.update_data(messages=messages)


async def select_underground_keyboard(stations: list[StationMini], direction: Literal['from', 'to']) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for station in stations:
        builder.button(
            text=f'{line_emojis.get(station.lineName, "🚈")} | «{station.name}» ({station.lineName})',
            callback_data=SelectUndergroundCallback(direction=direction, id=station.id)
        )
    builder.adjust(1, repeat=True)
    return builder.as_markup()


async def select_underground(station_id, direction, message: Message, state: FSMContext):
    station = StationMini(**requests.get(f'http://127.0.0.1:8080/station/mini/{station_id}').json())
    data = await state.get_data()

    if direction == "to" and station_id == data.get("from_station_underground"):
        response = await message.reply(
            "❌🔍 <b>Конечная станция не может совпадать со станцией отправления. Выберите другую станцию.</b>"
        )
        messages = data.get("messages", [])
        messages.append({'chat_id': response.chat.id, 'message_id': response.message_id})
        await state.update_data(messages=messages)
        return
    if direction == "from" and station_id == data.get("to_station_underground"):
        response = await message.reply(
            "❌🔍 <b>Станция отправления не может совпадать с конечной станцией. Выберите другую станцию.</b>"
        )
        messages = data.get("messages", [])
        messages.append({'chat_id': response.chat.id, 'message_id': response.message_id})
        await state.update_data(messages=messages)
        return

    await state.update_data({f'{direction}_station_underground': station_id})
    next_state = RouteSelectState.to_station_underground if direction == 'from' else None
    await state.set_state(next_state)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="↕ | Построить путь", callback_data="send_underground")]
        ]
    )
    if direction == 'from':
        response = await message.bot.send_message(
            message.chat.id,
            f'🚇🔍 <b>Выбрана станция «{station.name}» ({station.lineName}). Введите название станции КУДА вы отправляетесь.</b>'
        )
    else:
        response = await message.bot.send_message(
            message.chat.id,
            f'🚇🔍 <b>Выбрана станция «{station.name}» ({station.lineName}). Маршрут следования для построения пути установлен.</b>',
            reply_markup=keyboard
        )
        # Удаляем все предыдущие сообщения
        messages = data.get("messages", [])
        await delete_previous_messages(messages, message.bot, response.message_id, state)

    # Сохраняем ID нового сообщения
    messages = data.get("messages", [])
    messages.append({'chat_id': response.chat.id, 'message_id': response.message_id})
    await state.update_data(messages=messages)

@route_selector.callback_query(SelectUndergroundCallback.filter())
async def handle_select_underground(callback: CallbackQuery, callback_data: SelectUndergroundCallback, state: FSMContext):
    station_id = callback_data.id
    direction = callback_data.direction

    data = await state.get_data()

    if direction == "to" and station_id == data.get("from_station_underground"):
        await callback.message.edit_text(
            "❌🔍 <b>Конечная станция не может совпадать со станцией отправления. Выберите другую станцию.</b>",
            parse_mode="HTML"
        )
        return
    if direction == "from" and station_id == data.get("to_station_underground"):
        await callback.message.edit_text(
            "❌🔍 <b>Станция отправления не может совпадать с конечной станцией. Выберите другую станцию.</b>",
            parse_mode="HTML"
        )
        return

    station = StationMini(**requests.get(f'http://127.0.0.1:8080/station/mini/{station_id}').json())

    await state.update_data({f'{direction}_station_underground': station_id})

    next_state = RouteSelectState.to_station_underground if direction == 'from' else None
    await state.set_state(next_state)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="↕ | Построить путь", callback_data="send_underground")]
        ]
    )
    if direction == 'from':
        await callback.message.edit_text(
            f'🚇🔍 <b>Выбрана станция «{station.name}» ({station.lineName}). Введите название станции КУДА вы отправляетесь.</b>',
            parse_mode="HTML"
        )
    else:
        response = await callback.message.edit_text(
            f'🚇🔍 <b>Выбрана станция «{station.name}» ({station.lineName}). Маршрут следования для построения пути установлен.</b>', reply_markup=keyboard
        )
        messages = data.get("messages", [])
        await delete_previous_messages(messages, callback.bot, response.message_id, state)

@route_selector.callback_query(lambda c: c.data == 'find_underground_route')
async def find_route_underground(c: CallbackQuery, state: FSMContext):
    await state.set_state(RouteSelectState.from_station_underground)
    response = await c.message.edit_text('🚇🔍 <b>Введите название станции ОТКУДА вы отправляетесь.</b>')
    data = await state.get_data()
    messages = data.get('messages', [])
    messages.append({'chat_id': response.chat.id, 'message_id': response.message_id})
    await state.update_data(messages=messages)


@route_selector.message(RouteSelectState.from_station_underground)
async def select_from_underground(message: Message, state: FSMContext):
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
        await select_underground(stations[0].id, 'from', message, state)
    else:
        response = await message.bot.send_message(
            message.chat.id,
            f'🚇🔍 <b>Найдены следующие станции с похожим названием:</b>',
            reply_markup=await select_underground_keyboard(stations, 'from')
        )
        messages.append({'chat_id': response.chat.id, 'message_id': response.message_id})
        await state.update_data(messages=messages)


@route_selector.message(RouteSelectState.to_station_underground)
async def select_to_underground(message: Message, state: FSMContext):
    search_res = requests.get(f'http://127.0.0.1:8080/station/search?q={message.text}')
    data = await state.get_data()

    messages = data.get("messages", [])
    messages.append({'chat_id': message.chat.id, 'message_id': message.message_id})
    await state.update_data(messages=messages)

    if not search_res.ok:
        response = await message.reply(
            '❌🔍 <b>Станция с таким названием не найдена. Пожалуйста, укажите корректное название станции.</b>'
        )
        messages.append({'chat_id': response.chat.id, 'message_id': response.message_id})
        await state.update_data(messages=messages)
        return

    response_data = SearchResponse(**search_res.json())
    stations = response_data.stations

    if len(stations) == 1:
        await select_underground(stations[0].id, 'to', message, state)
    else:
        response = await message.bot.send_message(
            message.chat.id,
            f'🚇🔍 <b>Найдены следующие станции с похожим названием:</b>',
            reply_markup=await select_underground_keyboard(stations, 'to')
        )
        messages.append({'chat_id': response.chat.id, 'message_id': response.message_id})
        await state.update_data(messages=messages)

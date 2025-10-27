import logging
import os
from datetime import datetime, timedelta

import pytz
import requests
from babel.dates import format_date

from src.requests.get_weather_info import get_weather_title
from src.utils.load_config import load_config
from src.models.yandex.search_response import SearchResponse

config = load_config()


def search_buses(from_city: str, to_city: str, date: str, tz: str):
    search_request = requests.get(
        f"{os.getenv('YANDEX_API_URL')}/search?apikey={os.getenv('TOKEN_YANDEX')}&from={from_city}&to={to_city}&lang=ru_RU&date={date}&result_timezone={tz}&transport_types=bus&limit=250"
    )

    if not search_request.ok:
        logging.warning(f"API request error {search_request.text}")
        return None, None

    search = SearchResponse(**search_request.json())
    buses = search.segments
    info = search.search
    return buses, info


def format_bus_info(buses, info, date, tz_str):
    bus_info = []
    msg = ""

    for bus in buses:
        formatted_date = format_date(date, format='d MMMM', locale='ru_RU')
        timezone_now = datetime.now(tz_str)

        if bus.departure.astimezone(tz_str).date() > date.date():
            continue

        if timezone_now.timestamp() > bus.departure.timestamp():
            continue

        duration = bus.duration
        days, remainder = divmod(duration, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, _ = divmod(remainder, 60)

        if days > 0:
            duration_time = f'{int(days)} д. {int(hours)} час {int(minutes)} мин.'
        elif hours > 0:
            duration_time = f'{int(hours)} час {int(minutes)} мин.'
        else:
            duration_time = f'{minutes} мин.'

        ticket_price = "Неизвестно"
        if bus.tickets_info and bus.tickets_info.places:
            ticket_price = f'{bus.tickets_info.places[0].price.whole} рублей'

        time_until_arrival = bus.departure - timezone_now
        hours, remainder = divmod(time_until_arrival.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        if hours == 0 and minutes == 0:
            time_until_arrival_str = f'Выдвигается в путь'
        elif hours == 0:
            time_until_arrival_str = f'{minutes} мин.'
        else:
            time_until_arrival_str = f'{hours} час {minutes} мин.'

        this_bus_info = f'🚐 <b>| {bus.thread.title}</b>\n' \
                          f'<i>Отъезжает с «{bus.from_.title}» в {bus.departure.hour}:{bus.departure.minute:02d} по местному времени</i>\n' \
                          f'<i>Прибудет на «{bus.to.title}» в {bus.arrival.hour}:{bus.arrival.minute:02d} по местному времени</i>\n' \
                          f'<i>Время в пути составит: {duration_time}</i>\n' \
                          f'<i>Стоимость полного билета: {ticket_price}</i>\n' \
                          f'<i>Междугородний автобус | {bus.thread.carrier.title}</i>\n' \
                          f'<b>Время до отправления: {time_until_arrival_str}</b>\n'

        if len(msg + this_bus_info) > 900:
            break

        bus_info.append(this_bus_info)
        msg = f'🗓 <b>Расписание отправления междугородних автобусов «{info.from_.title}» ({get_weather_title(info.from_.title)}) – «{info.to.title}» ({get_weather_title(info.to.title)}) на {formatted_date}</b>\n\n' + '\n'.join(
            bus_info)
    return msg if bus_info else None


def get_intercity_bus_info(from_city: str, to_city: str, tz: str) -> str | None:
    tz_str = pytz.timezone(str(tz))
    date = datetime.now(tz_str)
    date_str = date.strftime('%Y-%m-%d')

    buses, info = search_buses(from_city, to_city, date_str, tz)
    if buses is None:
        return None

    msg = format_bus_info(buses, info, date, tz_str)
    if not msg:
        next_day = date + timedelta(days=1)
        next_day_str = next_day.strftime('%Y-%m-%d')
        buses, info = search_buses(from_city, to_city, next_day_str, tz)
        if buses is None:
            return None
        msg = format_bus_info(buses, info, next_day, tz_str)

    return msg
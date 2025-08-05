import logging
import os
from datetime import datetime, timedelta

import pytz
import requests
from babel.dates import format_date

from src.utils.load_config import load_config
from src.models.search_response import SearchResponse
from src.request.get_weather_info import get_weather_code
from src.utils.format_transport_subtype import format_transport_subtype

config = load_config()


def search_suburban(from_station: str, to_station: str, date: str, tz: str):
    search_request = requests.get(
        f"{os.getenv('YANDEX_API_URL')}/search?apikey={os.getenv('TOKEN_YANDEX')}&from={from_station}&to={to_station}&lang=ru_RU&date={date}&result_timezone={tz}&transport_types=suburban&limit=250"
    )

    if not search_request.ok:
        logging.warning(f"API request error {search_request.text}")
        return None, None

    search = SearchResponse(**search_request.json())
    suburbans = search.segments
    info = search.search
    return suburbans, info


def format_suburban_info(suburbans, info, date, tz_str, from_station, to_station, express):
    suburban_info = []
    msg = ""

    for suburban in suburbans:
        if suburban.departure.astimezone(tz_str).date() > date.date():
            continue

        formatted_date = format_date(date, format='d MMMM', locale='ru_RU')
        timezone_now = datetime.now(tz_str)

        if timezone_now.timestamp() > suburban.departure.timestamp():
            continue

        if express:
            if not suburban.thread.express_type == "express":
                continue

        transport_subtype = format_transport_subtype(suburban.thread.transport_subtype.title)
        carrier = suburban.thread.carrier.title

        if suburban.thread.number == "МЦК":
            transport_subtype = "Ласточка"

        emoji = config.suburban_map.get(carrier, config.suburban_map.get(transport_subtype, "🚆"))

        ticket_price = "Неизвестно"
        if suburban.tickets_info and suburban.tickets_info.places:
            ticket_price = f'{suburban.tickets_info.places[0].price.whole} рублей'

        departure_platform = suburban.departure_platform or "неизвестного пути"

        duration = suburban.duration
        hours, remainder = divmod(duration, 3600)
        minutes, _ = divmod(remainder, 60)

        if hours > 0:
            duration_time = f'{int(hours)} час {int(minutes)} мин.'
        else:
            duration_time = f'{int(minutes)} мин.'

        time_until_arrival = suburban.departure - timezone_now
        hours, remainder = divmod(time_until_arrival.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        if hours == 0 and minutes == 0:
            time_until_arrival_str = 'Прибывает на станцию'
        elif hours == 0:
            time_until_arrival_str = f'{minutes} мин.'
        else:
            time_until_arrival_str = f'{hours} час. {minutes} мин.'

        this_suburban_info = f'{emoji} <b>{suburban.thread.number} | {suburban.thread.title}</b>\n' \
                             f'<i>Отправляется с {departure_platform} в {suburban.departure.hour}:{suburban.departure.minute:02d}</i>\n' \
                             f'<i>С остановками: {suburban.stops}</i>\n' \
                             f'<i>Стоимость билета: {ticket_price}</i>\n' \
                             f'<i>Время в пути составит: {duration_time} ({suburban.arrival.hour}:{suburban.arrival.minute:02d})</i>\n' \
                             f'<i>{transport_subtype} | {suburban.thread.carrier.title}</i>\n' \
                             f'<b>Время до прибытия: {time_until_arrival_str}</b>\n'

        if len(msg + this_suburban_info) > 900:
            break

        suburban_info.append(this_suburban_info)
        msg = f'🗓 <b>Расписание пригородных поездов «{info.from_.title}» ({get_weather_code(from_station)}) – «{info.to.title}» ({get_weather_code(to_station)}) на {formatted_date}</b>\n\n' \
              + '\n'.join(suburban_info)
    return msg if suburban_info else None


def get_suburban_info(from_station: str, to_station: str, tz: str, express: bool) -> str | None:
    tz_str = pytz.timezone(str(tz))
    date = datetime.now(tz_str)
    date_str = date.strftime('%Y-%m-%d')

    suburbans, info = search_suburban(from_station, to_station, date_str, tz)
    if suburbans is None:
        return None

    msg = format_suburban_info(suburbans, info, date, tz_str, from_station, to_station, express)
    if not msg:
        next_day = date + timedelta(days=1)
        next_day_str = next_day.strftime('%Y-%m-%d')
        suburbans, info = search_suburban(from_station, to_station, next_day_str, tz)
        if suburbans is None:
            return None
        msg = format_suburban_info(suburbans, info, next_day, tz_str, from_station, to_station, express)

    return msg
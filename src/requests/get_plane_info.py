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


def search_planes(from_city: str, to_city: str, date: str, tz: str):
    search_request = requests.get(
        f"{os.getenv('YANDEX_API_URL')}/search?apikey={os.getenv('TOKEN_YANDEX')}&from={from_city}&to={to_city}&lang=ru_RU&date={date}&result_timezone={tz}&transport_types=plane&limit=250"
    )

    if not search_request.ok:
        logging.warning(f"API request error {search_request.text}")
        return None, None

    search = SearchResponse(**search_request.json())
    planes = search.segments
    info = search.search
    return planes, info


def format_plane_info(planes, info, date, tz_str):
    plane_info = []
    msg = ""

    for plane in planes:
        formatted_date = format_date(date, format='d MMMM', locale='ru_RU')
        timezone_now = datetime.now(tz_str)

        if plane.departure.astimezone(tz_str).date() > date.date():
            continue

        if timezone_now.timestamp() > plane.departure.timestamp():
            continue

        duration = plane.duration
        days, remainder = divmod(duration, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, _ = divmod(remainder, 60)

        if days > 0:
            duration_time = f'{int(days)} д. {int(hours)} час {int(minutes)} мин.'
        elif hours > 0:
            duration_time = f'{int(hours)} час {int(minutes)} мин.'
        else:
            duration_time = f'{minutes} мин.'

        time_until_arrival = plane.departure - timezone_now
        hours, remainder = divmod(time_until_arrival.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        if hours == 0 and minutes == 0:
            time_until_arrival_str = f'Вылетает с аэропорта «{plane.from_.title}»'
        elif hours == 0:
            time_until_arrival_str = f'Время до отправления: {minutes} мин.'
        else:
            time_until_arrival_str = f'Время до отправления: {hours} час {minutes} мин.'

        if hours == 0 and minutes <= 15:
            status_board = 'Посадка завершена (❌)'
        elif hours == 0 and minutes <= 40:
            status_board = 'Регистрация завершена (⚠)'
        elif hours <= 2:
            status_board = 'Регистрация на самолёт (✅)'
        else:
            status_board = 'Ожидается регистрация (⏳)'

        departure_airport = (
            f'Отлетает с терминала "{plane.departure_terminal}" аэропорта «{plane.from_.title}»'
            if plane.departure_terminal
            else f'Отлетает с аэропорта «{plane.from_.title}»'
        )
        departure_airport += f' в {plane.departure.hour}:{plane.departure.minute:02d} по местному времени'

        if not plane.thread.vehicle:
            vehicle = 'Самолёт'
        else:
            vehicle = plane.thread.vehicle

        arrival_airport = (
            f'Прилетает в терминал "{plane.arrival_terminal}" аэропорта «{plane.to.title}»'
            if plane.arrival_terminal
            else f'Прилетает в аэропорт «{plane.to.title}»'
        )
        arrival_airport += f' в {plane.arrival.hour}:{plane.arrival.minute:02d} по местному времени'

        this_plane_info = f'✈ <b>{plane.thread.number} | {plane.thread.title}</b>\n' \
                          f'<i>{departure_airport}</i>\n' \
                          f'<i>{arrival_airport}</i>\n' \
                          f'<i>Время полета составит: {duration_time}</i>\n' \
                          f'<i>{vehicle} | {plane.thread.carrier.title}</i>\n' \
                          f'<b>{status_board}</b>\n' \
                          f'<b>{time_until_arrival_str}</b>\n'

        if len(msg + this_plane_info) > 900:
            break

        plane_info.append(this_plane_info)
        msg = f'🗓 <b>Расписание отправления самолетов «{info.from_.title}» ({get_weather_title(info.from_.title)}) – «{info.to.title}» ({get_weather_title(info.to.title)}) на {formatted_date}</b>\n\n' + '\n'.join(
            plane_info)
    return msg if plane_info else None


def get_plane_info(from_city: str, to_city: str, tz: str) -> str | None:
    tz_str = pytz.timezone(str(tz))
    date = datetime.now(tz_str)
    date_str = date.strftime('%Y-%m-%d')

    planes, info = search_planes(from_city, to_city, date_str, tz)
    if planes is None:
        return None

    msg = format_plane_info(planes, info, date, tz_str)
    if not msg:
        next_day = date + timedelta(days=1)
        next_day_str = next_day.strftime('%Y-%m-%d')
        planes, info = search_planes(from_city, to_city, next_day_str, tz)
        if planes is None:
            return None
        msg = format_plane_info(planes, info, next_day, tz_str)

    return msg
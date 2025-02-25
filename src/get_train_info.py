import logging
import os
from datetime import datetime, timedelta

import pytz
import requests
from babel.dates import format_date
from dotenv import load_dotenv
from src.utils.load_config import load_config
from src.models.search_response_train import SearchResponse

load_dotenv()

token_yandex = os.getenv('TOKEN_YANDEX')
token_bot = os.getenv('TOKEN_BOT')

config = load_config()


def get_train_info(from_city: str, to_city: str, tz: str) -> str | None:
    tz_str = pytz.timezone(str(tz))
    date = datetime.now(tz_str).strftime('%Y-%m-%d')

    def search_trains(date):
        search_request = requests.get(
            f"https://api.rasp.yandex.net/v3.0/search?apikey={token_yandex}&from={from_city}&to={to_city}&lang=ru_RU&date={date}&result_timezone={tz}&transport_types=train&limit=250"
        )

        if not search_request.ok:
            logging.warning(f"API request error {search_request.text}")
            return None, None

        search = SearchResponse(**search_request.json())
        trains = search.segments
        info = search.search
        return trains, info

    def format_train_info(trains, date, tz_str):
        train_info = []
        msg = ""

        for train in trains:
            formatted_date = format_date(date, format='d MMMM', locale='ru_RU')
            timezone_now = datetime.now(tz_str)

            if train.departure.astimezone(tz_str).date() > date.date():
                continue

            if timezone_now.timestamp() > train.departure.timestamp():
                continue

            transport_subtype = "Поезд дальнего следования"
            if train.thread.transport_subtype.title:
                transport_subtype = f'{train.thread.transport_subtype.title}'

            carrier = train.thread.carrier.title
            if carrier == "РЖД/ДОСС" and transport_subtype != "«Ласточка»":
                transport_subtype = "«Сапсан»"
            emoji = config.train_map.get(carrier, config.train_map.get(transport_subtype, "🚂"))

            duration = train.duration
            days, remainder = divmod(duration, 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes, _ = divmod(remainder, 60)

            if days > 0:
                duration_time = f'{int(days)} день {int(hours)} час {int(minutes)} минут'
            elif hours > 0:
                duration_time = f'{int(hours)} час {int(minutes)} минут'
            else:
                duration_time = f'{minutes} минут'

            time_until_arrival = train.departure - timezone_now
            hours, remainder = divmod(time_until_arrival.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            if hours == 0 and minutes == 0:
                time_until_arrival_str = 'Отправляться от вокзала или пункта остановки'
            elif hours == 0:
                time_until_arrival_str = f'{minutes} минут'
            else:
                time_until_arrival_str = f'{hours} час {minutes} минут'

            this_train_info = f'{emoji} <b>{train.thread.number} | {train.thread.title}</b>\n' \
                              f'<i>Отправляется с {train.from_.title} в {train.departure.hour}:{train.departure.minute:02d} по местному времени</i>\n' \
                              f'<i>Прибудет в {train.to.title} в {train.arrival.hour}:{train.arrival.minute:02d} по местному времени</i>\n' \
                              f'<i>Время в пути составит: {duration_time}</i>\n' \
                              f'<i>{transport_subtype} | {train.thread.carrier.title}</i>\n' \
                              f'<b>Время до отправления: {time_until_arrival_str}</b>\n'

            if len(msg + this_train_info) > 900:
                break

            train_info.append(this_train_info)
            msg = f'🗓 <b>Расписание поездов дальнего следования «{info.from_.title}» – «{info.to.title}» на {formatted_date}</b>\n\n' + '\n'.join(
                train_info)
        return msg if train_info else None

    trains, info = search_trains(date)
    if trains is None:
        return None

    msg = format_train_info(trains, datetime.now(tz_str), tz_str)
    if not msg:
        next_day = datetime.now(tz_str) + timedelta(days=1)
        trains, info = search_trains(next_day.strftime('%Y-%m-%d'))
        if trains is None:
            return None
        msg = format_train_info(trains, next_day, tz_str)

    return msg
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


def get_train_info(from_city: str, to_city: str) -> str | None:
    date = datetime.now().strftime('%Y-%m-%d')
    formatted_date = format_date(datetime.now(), format='d MMMM', locale='ru_RU')
    # tomorrow_date = format_date(datetime.now() + timedelta(days=1), format='d MMMM', locale='ru_RU')
    moscow_tz = pytz.timezone('Europe/Moscow')
    moscow_now = datetime.now(moscow_tz)

    search_request = requests.get(
        f"https://api.rasp.yandex.net/v3.0/search?apikey={token_yandex}&from={from_city}&to={to_city}&lang=ru_RU&date={date}&transport_types=train&limit=250"
    )

    if not search_request.ok:
        logging.warning(f"API request error {search_request.text}")
        return None

    search = SearchResponse(**search_request.json())
    trains = search.segments
    info = search.search

    train_info = []
    msg = ""

    for train in trains:
        if moscow_now.timestamp() > train.departure.timestamp():
            continue

        transport_subtype = "Обычный поезд"
        if train.thread.transport_subtype.title:
            transport_subtype = f'{train.thread.transport_subtype.title}'

        carrier = train.thread.carrier.title
        emoji = config.train_map.get(carrier, config.train_map.get(transport_subtype, "🚂"))

        duration = train.duration
        hours, remainder = divmod(duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours == 0:
            duration_time = f'{minutes} минут'
        else:
            duration_time = f'{hours} час {minutes} минут'

        time_until_arrival = train.departure - moscow_now
        hours, remainder = divmod(time_until_arrival.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours == 0 and minutes == 0:
            time_until_arrival_str = 'Отправляться от вокзала'
        elif hours == 0:
            time_until_arrival_str = f'{minutes} минут'
        else:
            time_until_arrival_str = f'{hours} час {minutes} минут'

        msg = f'📋 <b>Расписание поездов от «{info.from_.title}» до «{info.to.title}» на {formatted_date}</b>\n\n' + '\n'.join(
            train_info)

        this_train_info = f'{emoji} <b>{train.thread.number} | {train.thread.title}</b>\n' \
                          f'<i>Отправляется с {train.from_.title} в {train.departure.hour}:{train.departure.minute:02d}</i>\n' \
                          f'<i>Прибудет в {train.to.title} в {train.arrival.hour}:{train.arrival.minute:02d}</i>\n' \
                          f'<i>Время в пути составит: {duration_time}</i>\n' \
                          f'<i>{transport_subtype} | {train.thread.carrier.title}</i>\n' \
                          f'<b>Время до отправления: {time_until_arrival_str}</b>\n'

        if len(msg + this_train_info) > 900:
            break

        train_info.append(
            this_train_info
        )
        msg = f'📋 <b>Расписание поездов от «{info.from_.title}» до «{info.to.title}» на {formatted_date}</b>\n\n' + '\n'.join(
            train_info)
    return msg if train_info else None

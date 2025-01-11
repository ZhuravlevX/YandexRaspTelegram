import logging
import os
from datetime import datetime, timedelta
import pytz
import requests
from babel.dates import format_date
from dotenv import load_dotenv
from src.utils.load_config import load_config
from src.models.search_response import SearchResponse

load_dotenv()

token_yandex = os.getenv('TOKEN_YANDEX')
token_bot = os.getenv('TOKEN_BOT')

config = load_config()


def get_train_info(from_station: str, to_station: str) -> str | None:
    date = datetime.now().strftime('%Y-%m-%d')
    formatted_date = format_date(datetime.now(), format='d MMMM', locale='ru_RU')
    tomorrow_date = format_date(datetime.now() + timedelta(days=1), format='d MMMM', locale='ru_RU')
    moscow_tz = pytz.timezone('Europe/Moscow')
    moscow_now = datetime.now(moscow_tz)

    search_request = requests.get(
        f"https://api.rasp.yandex.net/v3.0/search?apikey={token_yandex}&from={from_station}&to={to_station}&lang=ru_RU&date={date}&transport_types=suburban&limit=250"
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

        transport_subtype = train.thread.transport_subtype.title
        carrier = train.thread.carrier.title
        emoji = config.emoji_map.get(carrier, config.emoji_map.get(transport_subtype, "🚆"))

        ticket_price = "Неизвестно"
        if train.tickets_info and train.tickets_info.places:
            ticket_price = f'{train.tickets_info.places[0].price.whole} рублей'

        departure_platform = train.departure_platform
        if not departure_platform:
            departure_platform = "неизвестного пути"

        time_until_arrival = train.departure - moscow_now
        hours, remainder = divmod(time_until_arrival.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours == 0 and minutes == 0:
            time_until_arrival_str = 'Прибывает на станцию'
        elif hours == 0:
            time_until_arrival_str = f'{minutes} минут'
        else:
            time_until_arrival_str = f'{hours} час {minutes} минут'

        msg = f'📋 <b>Расписание поездов от «{info.from_.title}» до «{info.to.title}» на {formatted_date} по {tomorrow_date}</b>\n\n' + '\n'.join(
            train_info)

        this_train_info = f'{emoji} <b>{train.thread.number} | {train.thread.title}</b>\n' \
                          f'<i>Отправляется с {departure_platform} в {train.departure.hour}:{train.departure.minute:02d}</i>\n' \
                          f'<i>С остановками: {train.stops}</i>\n' \
                          f'<i>Стоимость билета: {ticket_price}</i>\n' \
                          f'<i>{transport_subtype.capitalize()} | {train.thread.carrier.title}</i>\n' \
                          f'<b>Время до прибытия: {time_until_arrival_str}</b>\n'

        if len(msg + this_train_info) > 900:
            break

        train_info.append(
            this_train_info
        )
        msg = f'📋 <b>Расписание поездов от «{info.from_.title}» до «{info.to.title}» на {formatted_date} по {tomorrow_date}</b>\n\n' + '\n'.join(
            train_info)
    return msg if train_info else None

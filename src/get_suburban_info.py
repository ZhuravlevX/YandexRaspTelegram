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


def get_suburban_info(from_station: str, to_station: str, tz: str) -> str | None:
    tz_str = pytz.timezone(str(tz))
    date = datetime.now(tz_str).strftime('%Y-%m-%d')

    def search_suburban(date):
        search_request = requests.get(
            f"https://api.rasp.yandex.net/v3.0/search?apikey={token_yandex}&from={from_station}&to={to_station}&lang=ru_RU&date={date}&result_timezone={tz}&transport_types=suburban&limit=250"
        )

        if not search_request.ok:
            logging.warning(f"API request error {search_request.text}")
            return None, None

        search = SearchResponse(**search_request.json())
        suburbans = search.segments
        info = search.search
        return suburbans, info

    def format_suburban_info(suburbans, date, tz_str):
        suburban_info = []
        msg = ""

        for suburban in suburbans:
            if suburban.departure.astimezone(tz_str).date() > date.date():
                continue

            formatted_date = format_date(date, format='d MMMM', locale='ru_RU')
            timezone_now = datetime.now(tz_str)

            if timezone_now.timestamp() > suburban.departure.timestamp():
                continue

            transport_subtype = suburban.thread.transport_subtype.title
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
                duration_time = f'{int(hours)} час {int(minutes)} минут'
            else:
                duration_time = f'{int(minutes)} минут'

            time_until_arrival = suburban.departure - timezone_now
            hours, remainder = divmod(time_until_arrival.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            if hours == 0 and minutes == 0:
                time_until_arrival_str = 'Прибывает на станцию'
            elif hours == 0:
                time_until_arrival_str = f'{minutes} минут'
            else:
                time_until_arrival_str = f'{hours} час {minutes} минут'

            this_suburban_info = f'{emoji} <b>{suburban.thread.number} | {suburban.thread.title}</b>\n' \
                              f'<i>Отправляется с {departure_platform} в {suburban.departure.hour}:{suburban.departure.minute:02d}</i>\n' \
                              f'<i>С остановками: {suburban.stops}</i>\n' \
                              f'<i>Стоимость билета: {ticket_price}</i>\n' \
                              f'<i>Время в пути составит: {duration_time}</i>\n' \
                              f'<i>{transport_subtype.capitalize()} | {suburban.thread.carrier.title}</i>\n' \
                              f'<b>Время до прибытия: {time_until_arrival_str}</b>\n'

            if len(msg + this_suburban_info) > 900:
                break

            suburban_info.append(this_suburban_info)
            msg = f'🗓 <b>Расписание пригородных поездов «{info.from_.title}» – «{info.to.title}» на {formatted_date}</b>\n\n' + '\n'.join(
                suburban_info)
        return msg if suburban_info else None

    suburbans, info = search_suburban(date)
    if suburbans is None:
        return None

    msg = format_suburban_info(suburbans, datetime.now(tz_str), tz_str)
    if not msg:
        next_day = datetime.now(tz_str) + timedelta(days=1)
        suburbans, info = search_suburban(next_day.strftime('%Y-%m-%d'))
        if suburbans is None:
            return None
        msg = format_suburban_info(suburbans, next_day, tz_str)

    return msg

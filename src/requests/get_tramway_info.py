import logging
import os

import requests

from src.utils.load_config import load_config
from src.models.mostrans.search_response_tramway import SearchResponse

config = load_config()


def search_tramway(id_stops):
    search_request = requests.get(
        f"{os.getenv("BACKEND_URL")}{os.getenv("PORT")}/mostrans/stop_info/c4c99fb1-05cf-485e-8526-91a528fe8952")

    if not search_request.ok:
        logging.warning(f"API request error {search_request.text.encode('UTF-8')}")
        return None, None

    info = SearchResponse(**search_request.json())
    tramway = info.routePath

    return tramway, info


def format_tramway_info(tramways, info, id_stops):
    tramway_info = []
    msg = ""

    for tramway in tramways:
        if not tramway.externalForecast:
            duration_time = "❌ Нету данных/Посадки нет"
        else:
            duration = tramway.externalForecast[0].time
            minutes, seconds = divmod(duration, 60)

            if duration == 0 or seconds == 0:
                duration_time = "Прибывает на остановку"
            elif minutes < 1:
                duration_time = f'Время до прибытия: {int(seconds)} сек.'
            elif minutes < 60:
                duration_time = f'Время до прибытия: {int(minutes)} мин. {int(seconds)} сек.'
            else:
                hours, minutes = divmod(minutes, 60)
                duration_time = f'Время до прибытия: {int(hours)} ч. {int(minutes)} мин.'

        this_tramway_info = f'🚊 <b>Трамвай {tramway.number} | «{tramway.lastStopName}»</b>\n' \
                            f'<i>Стоимость проезда по «Тройке»: 67 рублей</i>\n' \
                            f'<i>Витязь/Львенок | ГУП «Московский Метрополитен»/ГУП «Мосгортранс»</i>\n' \
                            f'<b>{duration_time}</b>\n'

        if len(msg + this_tramway_info) > 900:
            break

        tramway_info.append(this_tramway_info)
        msg = f'🗓 <b>Расписание трамваев от остановки «{info.name}»</b>\n\n' \
              + '\n'.join(tramway_info)
    return msg if tramway_info else None


def get_tramway_info(id_stops: str) -> str | None:
    tramways, info = search_tramway(id_stops)
    if tramways is None:
        return None

    msg = format_tramway_info(tramways, info, id_stops)
    if not msg:
        tramways, info = search_tramway(id_stops)
        if tramways is None:
            return None
        msg = format_tramway_info(tramways, info, id_stops)
    return msg

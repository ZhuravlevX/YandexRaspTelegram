import logging
import requests

from src.utils.load_config import load_config
from src.models.search_response_tramway import SearchResponse

config = load_config()

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0"}


def search_tramway(id_stops):
    search_request = requests.get(
        f"https://api.moscowapp.mos.ru/v8.2/stop_v2/474d0171-9ccd-415e-bf4b-74fa70ddeeab", headers=headers
    )

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
        duration = tramway.externalForecast[0].time
        minutes, seconds = divmod(duration, 60)

        if duration == 0 or seconds == 0:
            duration_time = "Прибывает на остановку"
        elif minutes < 1:
            duration_time = f'{int(seconds)} сек.'
        elif minutes < 60:
            duration_time = f'{int(minutes)} мин. {int(seconds)} сек.'
        else:
            hours, minutes = divmod(minutes, 60)
            duration_time = f'{int(hours)} ч. {int(minutes)} мин.'

        this_tramway_info = f'🚊 <b>Трамвай {tramway.number} | «{tramway.lastStopName}»</b>\n' \
                            f'<i>Стоимость проезда по «Тройке»: 67 рублей</i>\n' \
                            f'<i>Витязь/Львенок | ГУП «Московский Метрополитен»/ГУП «Мосгортранс»</i>\n' \
                            f'<b>Время до прибытия: {duration_time}</b>\n'

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

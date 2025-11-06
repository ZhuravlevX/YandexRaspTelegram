import logging
import os
import requests

from math import radians, sin, cos, sqrt, atan2
from src.models.mostrans.search_response_scooters import Scooters

operator_emojis = {
    "Yandex": "🟡",
    "WHOOSH": "🐝",
    "Urent": "🟪"
}

def get_scooters_info(lat: float, lon: float):
    delta_lat = 0.0018
    delta_lon = 0.0027

    lat1 = lat + delta_lat
    lon1 = lon - delta_lon
    lat2 = lat - delta_lat
    lon2 = lon + delta_lon

    raw = f"bounds?lat1={lat1}&lon1={lon1}&lat2={lat2}&lon2={lon2}"

    response = requests.get(f"{os.getenv("BACKEND_URL")}{os.getenv("PORT")}/mostrans/scooters/{raw}")
    scooters_info = []
    msg = ""

    if not response.ok:
        logging.warning(f"API request error: {response.text}")
        return None

    scooters_data = Scooters(**response.json())
    scooters = scooters_data.scooters

    for scooter in scooters:
        R = 6371000
        φ1, λ1, φ2, λ2 = map(radians, [lat, lon, scooter.lat, scooter.lng])
        dφ = φ2 - φ1
        dλ = λ2 - λ1

        a = sin(dφ / 2) ** 2 + cos(φ1) * cos(φ2) * sin(dλ / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        distance = R * c
        speed_mps = 1

        time_sec = distance / speed_mps
        time_min = time_sec / 60

        if time_sec <= 60:
            time = f'{time_sec:.0f} сек.'
        else:
            time = f'{time_min:.0f} мин.'

        if scooter.charge.percent >= 25:
            percent_charge = f'Заряд батареи: {scooter.charge.percent}% (🔋 ~{scooter.remainKm} км.)'
        else:
            percent_charge = f'Заряд батареи: {scooter.charge.percent}% (🪫 ~{scooter.remainKm} км.)'

        if scooter.organisation.name == 'Yandex':
            url_scooters = f'https://go.yandex/scooters?number={scooter.code}'
        elif scooter.organisation.name == 'WHOOSH':
            url_scooters = f'https://wsh.bike?s={scooter.code}'
        elif scooter.organisation.name == 'Urent':
            url_scooters = f'https://urs.su/a/{scooter.code}'

        this_scooters_info = f'<b>{operator_emojis.get(scooter.organisation.name, "❓")} {scooter.code} | Электросамокат {scooter.organisation.name}</b>\n' \
                             f'<i>{percent_charge}</i>\n' \
                             f'<i>{scooter.price}\n</i>' \
                             f'<i>Расстояние от вас до самоката {distance:.0f} м. (~{time})\n</i>' \
                             f'<b><a href="{url_scooters}">Отобразить или арендовать электросамокат</a></b>\n'

        if len(msg + this_scooters_info) > 900:
            break

        scooters_info.append((time_sec, this_scooters_info))
        scooters_info.sort(key=lambda x: x[0])
        msg = f'📍 <b>Ближайшие электросамокаты операторов по указанной вами точки местоположения</b>\n\n' \
              + '\n'.join(info for _, info in scooters_info)
    return msg if scooters_info else None

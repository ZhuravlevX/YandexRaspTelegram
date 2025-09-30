import os
from typing import List
import requests

from src.models.mosmetro.search_response_underground import RouterResponse, Part, StationMini, Wagons, Train


def get_train(station_id, next_station_id) -> Train | None:
    try:
        res = requests.get(f'{os.getenv("BACKEND_URL")}/wagons/{station_id}')
        if res.ok:
            wagons = Wagons(**res.json()).data
            for w in wagons.values():
                if w[0].prevStation != next_station_id:
                    return w[0]
        return None
    except:
        return None


def build_part(part: Part, last):
    if len(part.nodes) < 2: return ''
    first_station = part.nodes[0]
    msg = f'<b>Прибытие поезда на «{first_station.name}» ({first_station.lineName}): </b>'

    train = get_train(first_station.id, part.nodes[1].id)

    if train:
        duration = train.arrivalTime
        minutes, seconds = divmod(duration, 60)

        if minutes == 0:
            duration_time = f'{int(seconds)} сек.'
        elif seconds == 0 or duration == 0:
            duration_time = "Прибывает"
        else:
            duration_time = f'{int(minutes)} мин. {int(seconds)} сек.'

        load = ['' for i in train.wagons.keys()]
        for i, l in train.wagons.items():
            load[i - 1] = l
        msg += f'<b>{duration_time}</b>\n'

        load_counts = {
            'low': load.count('low'),
            'medium': load.count('medium'),
            'mediumHigh': load.count('mediumHigh'),
            'High': load.count('High')
        }

        priority = ['low', 'medium', 'mediumHigh', 'High']

        most_common_load = max(load_counts, key=lambda x: (load_counts[x], priority.index(x)))

        if most_common_load == 'low':
            msg += 'Вагоны свободны (🟢)\n'
        elif most_common_load == 'medium':
            msg += 'Вагоны умеренно свободны (🟡)\n'
        elif most_common_load == 'mediumHigh':
            msg += 'Вагоны умеренно заполнены (🟠)\n'
        elif most_common_load == 'High':
            msg += 'Вагоны заполнены (🔴)\n'
    else:
        msg += '<b>Неизвестно</b>\n'
        msg += 'Нету данных (⚪)\n'

    msg += f'<i>До {"конечной" if last else "пересадки"} – {part.duration // 60} мин.</i>\n\n'
    return msg


def stations_to_str(stations: List[StationMini]):
    s = f'<b><i>«{stations[0].name}»</i> ({stations[0].lineName}) ➡ <i>«{stations[-1].name}»</i> ({stations[-1].lineName})</b>'

    return s


def build_route_message(route: RouterResponse):
    msg = f'<b>↔ Путь от «{route.parts[0].nodes[0].name}» ({route.parts[0].nodes[0].lineName}) до «{route.parts[-1].nodes[-1].name}» ({route.parts[-1].nodes[-1].lineName})</b>\n\n<b><i>От</i></b> '
    for part in route.parts[:-1]:
        msg += stations_to_str(part.nodes)
        msg += ' ↪ '
    msg += stations_to_str(route.parts[-1].nodes)

    duration = route.duration
    hours, remainder = divmod(duration, 3600)
    minutes, _ = divmod(remainder, 60)

    if hours > 0 and minutes > 0:
        duration_time = f'{int(hours)} час {int(minutes)} мин.'
    elif hours > 0:
        duration_time = f'{int(hours)} час'
    else:
        duration_time = f'{int(minutes)} мин.'

    msg += f'\n<i>Общее время пути: {duration_time}</i>'
    msg += '\n\n'

    for part in route.parts[:-1]:
        msg += build_part(part, False)

    msg += build_part(route.parts[-1], True)

    return msg.strip() + f"\n"


def get_underground_info(from_station_underground: str, to_station_underground: str):
    try:
        res = requests.get(
            f'{os.getenv("BACKEND_URL")}{os.getenv("PORT")}/mosmetro/route?from={from_station_underground}&to={to_station_underground}'
        )
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return None

    if not res.ok:
        return None

    route = RouterResponse(**res.json())
    text = build_route_message(route)
    return text

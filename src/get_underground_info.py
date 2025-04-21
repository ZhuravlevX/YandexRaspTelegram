from typing import List
import requests

from src.models.metro_api import RouterResponse, Part, StationMini, Wagons, Train

load_emoji = {
    'low': '🟩',
    'medium': '🟨',
    'high': '🟥',
}


def get_train(station_id, next_station_id) -> Train | None:
    try:
        res = requests.get(f'http://127.0.0.1:8080/wagons/{station_id}')
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
    msg = f'<b>Время до прибытия поезда на станцию «{first_station.name}» ({first_station.lineName}): </b>'



    train = get_train(first_station.id, part.nodes[1].id)

    if train:
        duration = train.arrivalTime
        minutes, seconds = divmod(duration, 60)

        if minutes == 0:
            duration_time = f'{int(seconds)} секунд'
        elif seconds == 0:
            duration_time = "Поезд прибывает на станцию"
        else:
            duration_time = f'{int(minutes)} минут {int(seconds)} секунд'

        load = ['' for i in train.wagons.keys()]
        for i, l in train.wagons.items():
            load[i - 1] = l
        msg += f'<b>{duration_time}</b>\n'
        msg += '<i>Загруженность вагонов:</i>\n'
        msg += f'{"".join([load_emoji[l] for l in load])}\n'
    else:
        msg += '<b>Неизвестно</b>\n'
        msg += '<i>Загруженность вагонов:</i>\n'
        msg += '⬜⬜⬜⬜⬜⬜⬜\n'

    msg += f'<i>Ехать до {"конечной станции маршрута" if last else "станции пересадки"}: {part.duration // 60} минут</i>\n\n'
    return msg


def stations_to_str(stations: List[StationMini]):
    s = f'<b><i>«{stations[0].name}»</i> ({stations[0].lineName}) ➡ <i>«{stations[-1].name}»</i> ({stations[-1].lineName})</b>'

    return s


def build_route_message(route: RouterResponse):
    msg = f'<b>🚇↔ Маршрут следования от станции «{route.parts[0].nodes[0].name}» ({route.parts[0].nodes[0].lineName}) до станции «{route.parts[-1].nodes[-1].name}» ({route.parts[-1].nodes[-1].lineName})</b>\n\n<b><i>От</i></b> '
    for part in route.parts[:-1]:
        msg += stations_to_str(part.nodes)
        msg += ' ↪ '
    msg += stations_to_str(route.parts[-1].nodes)

    duration = route.duration
    hours, remainder = divmod(duration, 3600)
    minutes, _ = divmod(remainder, 60)

    if hours > 0:
        duration_time = f'{int(hours)} час {int(minutes)} минут'
    else:
        duration_time = f'{int(minutes)} минут'

    msg += f'\n<i>Время в пути составит: {duration_time}</i>'
    msg += '\n\n'

    for part in route.parts[:-1]:
        msg += build_part(part, False)

    msg += build_part(route.parts[-1], True)

    return msg.strip() + f"\n"


def get_underground_info(from_station_underground: str, to_station_underground: str):
    res = requests.get(f'http://127.0.0.1:8080/route?from={from_station_underground}&to={to_station_underground}')

    if not res.ok:
        return

    route = RouterResponse(**res.json())
    text = build_route_message(route)
    return text
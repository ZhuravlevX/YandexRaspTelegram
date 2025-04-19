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
    msg = f'Время до прибытия поезда на станцию «{first_station.name}» ({first_station.lineName}): '

    train = get_train(first_station.id, part.nodes[1].id)
    if train:
        load = ['' for i in train.wagons.keys()]
        for i, l in train.wagons.items():
            load[i - 1] = l
        msg += f'{train.arrivalTime}с\n'
        msg += 'Загруженность вагонов:\n'
        msg += f'{"".join([load_emoji[l] for l in load])}\n'
    else:
        msg += 'Неизвестно\n'
        msg += 'Загруженность вагонов:\n'
        msg += '🔲🔲🔲🔲🔲🔲🔲🔲'



    msg += f'Ехать до {"конечной станции маршрута" if last else "станции пересадки"}: {part.duration // 60} минут\n\n'
    return msg


def stations_to_str(stations: List[StationMini]):
    s = f'«{stations[0].name}» ({stations[0].lineName})  ➡️ «{stations[-1].name}» ({stations[-1].lineName})'

    return s


def build_route_message(route: RouterResponse):
    msg = f'Маршрут от станции «{route.parts[0].nodes[0].name}» ({route.parts[0].nodes[0].lineName}) до станции «{route.parts[-1].nodes[-1].name}» ({route.parts[-1].nodes[-1].lineName})\n\nОт '
    for part in route.parts[:-1]:
        msg += stations_to_str(part.nodes)
        msg += ' 🔄 '
    msg += stations_to_str(route.parts[-1].nodes)
    msg += '\n\n'

    for part in route.parts[:-1]:
        msg += build_part(part, False)

    msg += build_part(route.parts[-1], True)

    return msg + f'Время в пути займёт {route.duration // 60} минут'

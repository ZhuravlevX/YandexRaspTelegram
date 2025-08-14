import re
import requests
from src.models.tramways import Tramway
from src.models.router_tramway import Router

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0"
}


def find_number_tramway(number: str) -> list[Tramway]:
    found_tramways = []

    search_request = requests.get(
        f"https://api.moscowapp.mos.ru/v8.2/suggest?&query={number}&types=Route",
        headers=headers
    )
    data = Tramway(**search_request.json())

    search = re.sub(r"\W", '', number.lower().strip())

    for item in data.data:
        if item.name != "Трамвай":
            continue
        if item.route.number.lower().startswith(search):
            found_tramways.append(item)

    return found_tramways


def find_end_route_tramway(id_route: str) -> list:
    search_request = requests.get(
        f"https://api.moscowapp.mos.ru/v8.2/route_v3/{id_route}",
        headers=headers
    )
    if not search_request.ok:
        print(f"Ошибка запроса: {search_request.status_code}")
        return []

    try:
        router = Router(**search_request.json())
    except Exception as ex:
        print(f"Ошибка парсинга: {ex}")
        return []

    result = []
    for direction in router.directions:
        for path in direction.routePaths:
            result.append({
                "endStopName": path.endStopName,
                "id": path.id
            })
    return result


def find_stops_tramway(id_route: str, select_endStop_id: str) -> list:
    search_request = requests.get(
        f"https://api.moscowapp.mos.ru/v8.2/route_v3/{id_route}",
        headers=headers
    )
    if not search_request.ok:
        print(f"Ошибка запроса: {search_request.status_code}")
        return []

    try:
        router = Router(**search_request.json())
    except Exception as ex:
        print(f"Ошибка парсинга: {ex}")
        return []

    stops = []
    for direction in router.directions:
        for path in direction.routePaths:
            if path.id == select_endStop_id:
                for stop in path.stops:
                    stops.append({
                        "id": stop.id,
                        "name": stop.name,
                        "endStopName": path.endStopName
                    })
    return stops


if __name__ == "__main__":
    print(find_number_tramway(input()))
    id_route = input("Введите id маршрута трамвая: ")
    ends = find_end_route_tramway(id_route)
    for end in ends:
        print(f'Направление: {end["endStopName"]} — ID: {end["id"]}')
    direction_id = input("Введите id направления (routePaths.id): ")
    print(find_stops_tramway(id_route, direction_id))
    # for stop in stops:
    #     print(f'{stop["name"]} — ID: {stop["id"]} | Конечная: {stop["endStopName"]}')

import os.path
import re

from pydantic import TypeAdapter

from src.models.stations import Station
from src.route_select.generate_stations_list import generate_stations_list


def find_station(title: str) -> list[Station]:
    found_stations = []

    if not os.path.isfile('./stations.json'):
        generate_stations_list()

    search = re.sub(r"\W", '', title.lower().strip())
    stations_type_adapter = TypeAdapter(dict[str, Station])
    with open('./stations.json', 'r', encoding='utf-8') as f:
        stations = stations_type_adapter.validate_json(f.read())

    for title, station in stations.items():
        if title.startswith(search):
            found_stations.append(station)

    return found_stations


if __name__ == '__main__':
    print(find_station(input()))

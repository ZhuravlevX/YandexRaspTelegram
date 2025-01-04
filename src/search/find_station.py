import json
import os.path
import re

from src.search.generate_stations_list import generate_stations_list


def find_station_code(title: str) -> list[dict[str, str]]:
    found_stations = []

    if not os.path.isfile('./stations.json'):
        generate_stations_list()

    search = re.sub(r"\W", '', title.lower().strip())
    with open('./stations.json', 'r', encoding='utf-8') as f:
        stations = json.loads(f.read())

    for title, station in stations.items():
        if title.startswith(search):
            found_stations.append(station)

    return found_stations

if __name__ == '__main__':
    print(find_station_code(input()))

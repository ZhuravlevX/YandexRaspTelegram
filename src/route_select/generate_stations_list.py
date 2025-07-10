import json
import os
import re

import requests

from src.models.stations_list_response import StationsListResponse


def find_stations() -> dict[str, dict[str, str]]:
    response = requests.get(
        f'{os.getenv('YANDEX_API_URL')}/stations_list/?apikey={os.getenv('TOKEN_YANDEX')}&lang=ru_RU&format=json')

    if response.status_code != 200:
        raise Exception('Failed to get station list')

    search_stations = StationsListResponse(**response.json())
    stations = {}

    for country in search_stations.countries:
        if not (country.title == 'Беларусь' or country.title == 'Россия'):
            continue
        for region in country.regions:
            for settlement in region.settlements:
                for station in settlement.stations:
                    if not (station.transport_type == 'train' or station.station_type == 'airport'):
                        continue

                    if not station.latitude and station.longitude == "":
                        continue

                    title = station.title.lower()
                    title = re.sub(r"\W", '', title)
                    code = station.codes.yandex_code
                    if title in stations:
                        title += '_' + code
                    if not code: continue

                    stations[title] = {
                        "title": station.title,
                        "latitude": station.latitude,
                        "longitude": station.longitude,
                        "code": code,
                        "region": region.title,
                        "station_type": station.station_type,
                    }
    return stations


def generate_stations_list():
    with open('./stations.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(find_stations(), indent=2, ensure_ascii=False))


if __name__ == '__main__':
    generate_stations_list()

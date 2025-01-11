import json
import os
import re

import requests
from dotenv import load_dotenv

from src.models.stations_list_response import StationsListResponse

load_dotenv()
token_yandex = os.getenv('TOKEN_YANDEX')
token_bot = os.getenv('TOKEN_BOT')


def find_stations() -> dict[str, dict[str, str]]:
    response = requests.get(
        f'https://api.rasp.yandex.net/v3.0/stations_list/?apikey={token_yandex}&lang=ru_RU&format=json')

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
                    if station.transport_type != 'train':
                        continue
                    title = station.title.lower()
                    title = re.sub(r"\W", '', title)
                    code = station.codes.yandex_code
                    if title in stations:
                        title += '_' + code
                    if not code: continue

                    stations[title] = {
                        "title": station.title,
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

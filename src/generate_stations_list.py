import json
import re
import requests

from main import token_yandex


def find_stations() -> dict[str, str]:
    response = requests.get(
        f'https://api.rasp.yandex.net/v3.0/stations_list/?apikey={token_yandex}&lang=ru_RU&format=json')
    if response.status_code != 200:
        raise Exception('Failed to get station list')
    stations_list = response.json()
    stations = {}

    for country in stations_list['countries']:
        for region in country['regions']:
            for settlement in region['settlements']:
                for station in settlement['stations']:
                    if station['transport_type'] != 'train':
                        continue
                    title = station['title'].lower()
                    title = re.sub(r"\W", '', title)

                    code = station['codes']['yandex_code']

                    if title in stations:
                        title += code
                    stations[title] = code

    return stations


def generate_stations_list():
    with open('./stations.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(find_stations(), indent=2, ensure_ascii=False))

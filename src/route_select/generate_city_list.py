import json
import os
import re

import requests
from dotenv import load_dotenv

from src.models.stations_list_response import StationsListResponse

load_dotenv()
token_yandex = os.getenv('TOKEN_YANDEX')
token_bot = os.getenv('TOKEN_BOT')


def find_city() -> dict[str, dict[str, str]]:
    response = requests.get(
        f'https://api.rasp.yandex.net/v3.0/stations_list/?apikey={token_yandex}&lang=ru_RU&format=json')

    if response.status_code != 200:
        raise Exception('Failed to get station list')

    search_city = StationsListResponse(**response.json())
    city = {}

    for country in search_city.countries:
        if not (country.title == 'Беларусь' or country.title == 'Россия'):
            continue
        for region in country.regions:
            for settlement in region.settlements:
                title = settlement.title.lower()
                title = re.sub(r"\W", '', title)
                code = settlement.codes.yandex_code
                if title in city:
                    title += '_' + code
                if not code: continue

                city[title] = {
                    "region": settlement.title,
                    "code": code,
                }
    return city


def generate_city_list():
    with open('./cities.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(find_city(), indent=2, ensure_ascii=False))


if __name__ == '__main__':
    generate_city_list()
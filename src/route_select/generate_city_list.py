import json
import os
import re

import requests

from src.models.stations_list_response import StationsListResponse


def find_city() -> dict[str, dict[str, str]]:
    response = requests.get(
        f'{os.getenv("YANDEX_API_URL")}/stations_list/?apikey={os.getenv('TOKEN_YANDEX')}&lang=ru_RU&format=json')

    if response.status_code != 200:
        raise Exception('Failed to get station list')

    search_city = StationsListResponse(**response.json())
    city = {}

    for country in search_city.countries:
        if country.title not in ['Беларусь', 'Россия', 'Северная Корея', 'Казахстан', 'Китай', 'Монголия']:
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
                    "country": country.title,
                    "code": code,
                }
    return city


def generate_city_list():
    with open('./cities.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(find_city(), indent=2, ensure_ascii=False))


if __name__ == '__main__':
    generate_city_list()

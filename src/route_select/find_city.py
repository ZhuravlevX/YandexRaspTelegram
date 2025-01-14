import os.path
import re

from pydantic import TypeAdapter

from src.models.cities import City
from src.route_select.generate_city_list import generate_city_list


def find_city(title: str) -> list[City]:
    found_cities = []

    if not os.path.isfile('./cities.json'):
        generate_city_list()

    search = re.sub(r"\W", '', title.lower().strip())
    cities_type_adapter = TypeAdapter(dict[str, City])
    with open('./cities.json', 'r', encoding='utf-8') as f:
        cities = cities_type_adapter.validate_json(f.read())

    for title, city in cities.items():
        if title.startswith(search):
            found_cities.append(city)

    return found_cities


if __name__ == '__main__':
    print(find_city(input()))

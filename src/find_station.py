import json
import os.path
import re
from typing import Union

from generate_stations_list import generate_stations_list


def find_station_code(title: str) -> Union[str, None]:
    if not os.path.isfile('./stations.json'):
        generate_stations_list()

    search = re.sub(r"\W", '', title.lower().strip())
    with open('./stations.json', 'r', encoding='utf-8') as f:
        stations = json.loads(f.read())

    for title, code in stations.items():
        if title.startswith(search):
            print(title, code)
            # return code

    return None


print(find_station_code(input()))

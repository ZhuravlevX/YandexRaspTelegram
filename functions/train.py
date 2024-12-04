import os
import requests
import json

config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')

with open(config_path, 'r') as config_file:
    config = json.load(config_file)

token_yandex = config.get('token_yandex')
api_url = f'https://api.rasp.yandex.net/v3.0/stations_list/?apikey={token_yandex}&lang=ru_RU&format=json'

def find_station_code(api_url, station_title):
    response = requests.get(api_url)
    if response.status_code == 200:
        json_data = response.json()
        for country in json_data['countries']:
            for region in country['regions']:
                for settlement in region['settlements']:
                    for station in settlement['stations']:
                        if station['title'] == station_title:
                            return station['codes'].get('yandex_code')
    return None

station_title = input("Введите название станции: ")
station_code = find_station_code(api_url, station_title)

if station_code:
    print(f"Код станции '{station_title}': {station_code}")
else:
    print(f"Станция '{station_title}' не найдена.")

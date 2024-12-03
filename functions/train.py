import requests
import json

# Загрузка конфигурационного файла
with open('config.json', 'r') as config_file:
    config = json.load(config_file)
token_yandex = config.get('token_yandex')
api_url = f'https://api.rasp.yandex.net/v3.0/stations_list/?apikey={token_yandex}&lang=ru_RU&format=json'

# Функция для поиска кода станции по названию
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

# Пример использования
station_title = input("Введите название станции: ")
station_code = find_station_code(api_url, station_title)

if station_code:
    print(f"Код станции '{station_title}': {station_code}")
else:
    print(f"Станция '{station_title}' не найдена.")

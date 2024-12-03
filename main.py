from datetime import datetime
import time
import requests

api_key = "key"

rasp = requests.get(
    "https://api.rasp.yandex.net/v3.0/search?apikey={api_key}&lang=ru_RU&date=2024-12-02T23:25:41.014Z&transport_types=suburban"
)

trains = rasp.json()["segments"]

for train in trains:
    dep = datetime.fromisoformat(train["departure"])
    arr = datetime.fromisoformat(train["arrival"])

    if time.time() > dep.timestamp():
        continue
    print(
        f'{train["thread"]["number"]} {train["thread"]["title"]} {dep.hour}:{dep.minute:02d} - {arr.hour}:{arr.minute:02d}'
    )

from datetime import datetime
import time
import requests

rasp = requests.get(
    "https://api.rasp.yandex.net/v3.0/search?apikey=f6e22679-19c4-4979-9a23-43e4b96f163c&from=s9601636&to=s2000003&lang=ru_RU&date=2024-12-02T23:25:41.014Z&transport_types=suburban"
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
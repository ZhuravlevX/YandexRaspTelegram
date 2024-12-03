import json
import time
import requests
from datetime import datetime
from aiogram import Bot, Dispatcher, executor, types

API_TOKEN = '7651406999:AAGKO-d7W_HfcE5hRKCiO1fo4qKUP_cSGg8'

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


# Функция для получения расписания поездов
def get_trains():
    rasp = requests.get(
        "https://api.rasp.yandex.net/v3.0/search?apikey=f6e22679-19c4-4979-9a23-43e4b96f163c&from=s9601636&to=s2000003&lang=ru_RU&date=2024-12-03&transport_types=suburban&limit=200"
    )
    trains = rasp.json()["segments"]

    train_info = []
    count = 0

    for train in trains:
        dep = datetime.fromisoformat(train["departure"])
        arr = datetime.fromisoformat(train["arrival"])

        if time.time() > dep.timestamp():
            continue

        train_info.append(
            f'{train["thread"]["number"]} {train["thread"]["title"]} {dep.hour}:{dep.minute:02d} - {arr.hour}:{arr.minute:02d}'
        )

        count += 1
        if count >= 5:
            break

    return "\n".join(train_info)


# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Привет! Введите команду /trains, чтобы получить расписание поездов.")


# Обработчик команды /trains
@dp.message_handler(commands=['trains'])
async def send_trains(message: types.Message):
    train_info = get_trains()
    await message.reply(train_info if train_info else "Нет доступных поездов.")


# Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

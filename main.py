import json
import time
import requests
from datetime import datetime
import pytz
import asyncio
import random
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto

with open('config.json', 'r') as config_file:
    config = json.load(config_file)
token_yandex = config.get('token_yandex')
token_bot = config.get('token_bot')

api_url = f'https://api.rasp.yandex.net/v3.0/stations_list/?apikey={token_yandex}&lang=ru_RU&format=json'

bot = Bot(token=token_bot)
dp = Dispatcher(bot)


image_urls = [
    'https://rozklad.spb.ru/images/articles/dlya-chego-nuzhna-elektrichka.jpg',
    'https://www.msk-guide.ru/img/11971/MskGuide.ru_165366big.jpg',
    'https://s0.rbk.ru/v6_top_pics/media/img/0/76/756708342242760.jpg',
    'https://il.vgoroden.ru/l1fld9iyzhr5u_13xgtnz.jpeg',
    'https://tmholding.ru/upload/iblock/9ef/9ef8fa7cb1c2c46d3188a312d6cb5d9a.jpg'
]


auto_update = True
auto_update_active = False

def get_trains():
    date = datetime.now().strftime('%Y-%m-%d')
    moscow_tz = pytz.timezone('Europe/Moscow')
    moscow_now = datetime.now(moscow_tz)

    rasp = requests.get(
        f"https://api.rasp.yandex.net/v3.0/search?apikey={token_yandex}&from=s9601636&to=s2000003&lang=ru_RU&date={date}&transport_types=suburban&limit=131"
    )
    trains = rasp.json().get("segments", [])
    info = rasp.json().get("search", {})

    train_info = []
    count = 0

    from_title = info.get("from", {}).get("title", "Не указано")
    to_title = info.get("to", {}).get("title", "Не указано")

    for train in trains:
        dep = datetime.fromisoformat(train["departure"])
        arr = datetime.fromisoformat(train["arrival"])

        if moscow_now.timestamp() > dep.timestamp():
            continue

        ticket_price = "Неизвестная стоимость"
        if train.get("tickets_info") and train["tickets_info"].get("places"):
            place_info = train["tickets_info"]["places"][0]
            if place_info.get("price"):
                ticket_price = f'{place_info["price"].get("whole", "Неизвестная стоимость")} рублей'

        train_info.append(
            f'🚆 <b>{train["thread"]["number"]} {train["thread"]["title"]}</b>\n'
            f'<i>Отправляется с {train.get("departure_platform", "Не указано")} в {dep.hour}:{dep.minute:02d}</i>\n'
            f'<i>С остановками: {train.get("stops", "Не указано")}</i>\n'
            f'<i>Стоимость билета: {ticket_price}</i>\n'
            f'<i>{train["thread"].get("transport_subtype", {}).get("title", "Пригородный поезд")} | {train["thread"]["carrier"]["title"]}</i>\n'
        )

        count += 1
        if count >= 4:
            break

    if train_info:
        return f"📋 <b>Расписание поездов от \"{from_title}\" до \"{to_title}\" на {date}</b>\n\n" + "\n".join(train_info)
    else:
        return None


async def update_trains(message: types.Message):
    global auto_update, auto_update_active
    remaining_time = 60
    auto_update_active = True

    for i in range(60):
        current_time = datetime.now().strftime('%H:%M')
        train_info = get_trains()
        random_image = random.choice(image_urls)

        if not auto_update:
            train_info += f"\n🚆🚫<b>Автообновление было отменено. Последние данные были обновлены в {current_time}.</b>"
            media = InputMediaPhoto(media=random_image, caption=train_info, parse_mode='HTML')
            await message.edit_media(media)
            auto_update_active = False
            return

        if train_info:
            if i < 59:
                remaining_time -= 1
                additional_text = f"\n<b>🚆⌛ Следующее обновление через 1 минуту. Оставшееся время обновления: {remaining_time} минут.</b>"
            else:
                additional_text = f"\n<b>🚆⌛ Автообновление было завершено в {current_time}, учтите актуальность данного расписания!</b>"

            train_info += additional_text
            keyboard = InlineKeyboardMarkup().add(
                InlineKeyboardButton("🚫 | Отменить автообновление", callback_data="cancel_update"))
            media = InputMediaPhoto(media=random_image, caption=train_info, parse_mode='HTML')
            await message.edit_media(media, reply_markup=keyboard)
        else:
            await message.edit_text(
                "🚆🚫 <b>На текущий момент, на данную дату или заданому маршруту мы не нашли расписание. Пожалуйста, укажите текущую или же дальнейшую дату для расписания и проверьте, правильно ли вы указали названия станций для маршрута.</b>",
                parse_mode='HTML')
        await asyncio.sleep(60)

    auto_update_active = False

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Привет! Введите команду /trains, чтобы получить расписание поездов.")


@dp.message_handler(commands=['trains'])
async def send_trains(message: types.Message):
    global auto_update, auto_update_active

    if auto_update_active:
        await message.reply("🚆📋 <b>Расписание с автообновление на данный момент активно. Пожалуйста, отключите текущее автообновление перед запуском нового расписания.</b>", parse_mode='HTML')
        return

    auto_update = True
    initial_message = await message.reply("🚆📋 <b>Получаем расписание поездов...</b>", parse_mode='HTML')
    await update_trains(initial_message)


@dp.callback_query_handler(lambda c: c.data == 'cancel_update')
async def cancel_update(callback_query: types.CallbackQuery):
    global auto_update
    auto_update = False
    await bot.answer_callback_query(callback_query.id,
    text="🚫⌛ Автообновление было отменено, учтите что данные могут быть неактуальными. Отмена произойдет в течении минуты.")
    await bot.edit_message_reply_markup(callback_query.message.chat.id, callback_query.message.message_id, reply_markup=None)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

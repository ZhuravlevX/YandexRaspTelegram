import json
import time
import requests
from datetime import datetime
import pytz
import asyncio
import random
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
import logging

with open('config.json', 'r') as config_file:
    config = json.load(config_file)
token_yandex = config.get('token_yandex')
token_bot = config.get('token_bot')

api_url = f'https://api.rasp.yandex.net/v3.0/stations_list/?apikey={token_yandex}&lang=ru_RU&format=json'

bot = Bot(token=token_bot)
dp = Dispatcher(bot)

logging.basicConfig(level=logging.INFO)

image_urls = [
    'https://rozklad.spb.ru/images/articles/dlya-chego-nuzhna-elektrichka.jpg',
    'https://www.msk-guide.ru/img/11971/MskGuide.ru_165366big.jpg',
    'https://s0.rbk.ru/v6_top_pics/media/img/0/76/756708342242760.jpg',
    'https://tmholding.ru/upload/iblock/9ef/9ef8fa7cb1c2c46d3188a312d6cb5d9a.jpg',
    'https://moscowchanges.ru/wp-content/uploads/2019/10/IMG_0485.jpg',
    'https://i.ytimg.com/vi/Rqy7pN_ArXY/maxresdefault.jpg',
    'https://upload.wikimedia.org/wikipedia/commons/a/a0/ED2T-0041-hero.jpg',
    'https://railgallery.ru/photo/00/34/29/34297.jpg'
]

auto_update_users = {}
current_messages = {}

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

async def update_trains(message: types.Message, user_id: int):
    global auto_update_users, current_messages
    remaining_time = 60
    auto_update_users[user_id] = True
    current_messages[user_id] = message

    for i in range(60):
        current_time = datetime.now().strftime('%H:%M')
        train_info = get_trains()
        random_image = random.choice(image_urls)

        if not auto_update_users[user_id]:
            train_info += f"\n🚆🚫<b> Автообновление было отменено. Последние данные были обновлены в {current_time}.</b>"
            media = InputMediaPhoto(media=random_image, caption=train_info, parse_mode='HTML')
            await message.edit_media(media)
            auto_update_users[user_id] = False
            return

        if train_info:
            if i < 59:
                remaining_time -= 1
                additional_text = f"\n<b>🚆⌛ Следующее обновление через 1 минуту. Оставшееся время обновления: {remaining_time} минут.</b>"
            else:
                additional_text = f"\n<b>🚆⌛ Автообновление было завершено в {current_time}, учтите актуальность данного расписания!</b>"

            train_info += additional_text
            keyboard = InlineKeyboardMarkup().add(
                InlineKeyboardButton("🚫 | Отменить автообновление", callback_data=f"cancel_update_{user_id}"))
            media = InputMediaPhoto(media=random_image, caption=train_info, parse_mode='HTML')
            await message.edit_media(media, reply_markup=keyboard)
        else:
            await message.edit_text(
                "🚆🚫 <b>На текущий момент, на данную дату или заданому маршруту мы не нашли расписание. Пожалуйста, укажите текущую или же дальнейшую дату для расписания и проверьте, правильно ли вы указали названия станций для маршрута.</b>",
                parse_mode='HTML')
        await asyncio.sleep(60)

    auto_update_users[user_id] = False

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("⬅ | Указать маршрут", callback_data="button1"),
        InlineKeyboardButton("📋 | Узнать расписание", callback_data="button2")
    )
    random_image = random.choice(image_urls)
    await message.answer_photo(photo=random_image, caption="📋 <b>Расписание пригородных электричек и экспрессов</b>\n\n"
                               "Данный бот позволяет вам быстро узнать расписание об вашем поезде. Для этого нужно лишь указать откуда и куда вам надо приехать и появиться полная информация об ближащих пригородных электричек и поездах.\n\n"
                               "Для того, чтобы изменить или узнать расписание по текущим указаниям маршрута, нажмите кнопки ниже.", parse_mode='HTML', reply_markup=keyboard)

@dp.message_handler(commands=['trains'])
async def send_trains(message: types.Message):
    global auto_update_users, current_messages
    user_id = message.from_user.id

    if auto_update_users.get(user_id, False):
        await message.reply("🚆📋 <b>Расписание с автообновление на данный момент активно. Пожалуйста, отключите текущее автообновление перед запуском нового расписания.</b>", parse_mode='HTML')
        return

    initial_message = await message.reply("🚆📋 <b>Получаем расписание поездов...</b>", parse_mode='HTML')
    await update_trains(initial_message, user_id)

@dp.callback_query_handler(lambda c: c.data.startswith('cancel_update_'))
async def cancel_update(callback_query: types.CallbackQuery):
    global auto_update_users
    user_id = int(callback_query.data.split('_')[-1])
    auto_update_users[user_id] = False
    await bot.answer_callback_query(callback_query.id,
    text="🚫⌛ Автообновление было отменено, учтите что данные могут быть неактуальными. Отмена произойдет в течении минуты.")
    await bot.edit_message_reply_markup(callback_query.message.chat.id, callback_query.message.message_id, reply_markup=None)

@dp.callback_query_handler(lambda c: c.data == "button2")
async def handle_button2(callback_query: types.CallbackQuery):
    await send_trains(callback_query.message)

async def on_shutdown(dp):
    global current_messages
    for user_id, message in current_messages.items():
        current_time = datetime.now().strftime('%H:%M')
        await bot.send_message(message.chat.id, f"\n🚆🚫 <b>Бот остановил свою работу. Это связано с техническими работами и ошибками. Последнее автообновление вашего расписания было в {current_time}. Будьте внимательны и следите за расписанием!</b>", parse_mode='HTML')
    await dp.storage.close()
    await dp.storage.wait_closed()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_shutdown=on_shutdown)

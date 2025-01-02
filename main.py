import asyncio
import json
import locale
import logging
import random
from datetime import datetime, timedelta
import pytz
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, Message
from babel.dates import format_date
from dotenv import load_dotenv
import os

from src.find_station import find_station_code

locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

load_dotenv()
token_yandex = os.getenv('TOKEN_YANDEX')
token_bot = os.getenv('TOKEN_BOT')


with open('config.json', 'r') as config_file:
    config = json.load(config_file)
# token_yandex = config.get('token_yandex')
# token_bot = config.get('token_bot')
image_urls = config.get('image_urls')

api_url = f'https://api.rasp.yandex.net/v3.0/stations_list/?apikey={token_yandex}&lang=ru_RU&format=json'

dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

auto_update_users = {}
current_messages = {}

from_station = "s2000005"
to_station = "s9600216"


def get_trains():
    date = datetime.now().strftime('%Y-%m-%d')
    formatted_date = format_date(datetime.now(), format='d MMMM', locale='ru_RU')
    tomorrow_date = format_date(datetime.now() + timedelta(days=1), format='d MMMM', locale='ru_RU')
    moscow_tz = pytz.timezone('Europe/Moscow')
    moscow_now = datetime.now(moscow_tz)

    rasp = requests.get(
        f"https://api.rasp.yandex.net/v3.0/search?apikey={token_yandex}&from={from_station}&to={to_station}&lang=ru_RU&date={date}&transport_types=suburban&limit=250"
    )
    trains = rasp.json().get("segments", [])
    info = rasp.json().get("search", {})

    train_info = []
    count = 0

    from_title = info.get("from", {}).get("title", "Не указано")
    to_title = info.get("to", {}).get("title", "Не указано")

    emoji_map = {
        "Экспресс": "🚅",
        "экспресс РЭКС": "🚅",
        "Пригородный поезд": "🚆",
        "Стандарт плюс": "🚆✳️",
        "Ласточка": "🚆🕊",
        "Ласточка «Экспресс»": "🚅🕊",
        "Ласточка «Экспресс»  - состав 5 вагонов": "🚅🕊5️⃣",
        "Состав 4-6 вагонов": "🚆🔢",
        "Иволга": "🚆🐦",
        "Аэроэкспресс": "🚅🔴"
    }

    for train in trains:
        dep = datetime.fromisoformat(train["departure"])
        # arr = datetime.fromisoformat(train["arrival"])

        if moscow_now.timestamp() > dep.timestamp():
            continue

        transport_subtype = train["thread"].get("transport_subtype", {}).get("title", "Пригородный поезд")
        carrier = train["thread"].get("carrier", {}).get("title", {})
        emoji = emoji_map.get(carrier, emoji_map.get(transport_subtype,  "🚆"))

        ticket_price = "Неизвестная стоимость"
        if train.get("tickets_info") and train["tickets_info"].get("places"):
            place_info = train["tickets_info"]["places"][0]
            if place_info.get("price"):
                ticket_price = f'{place_info["price"].get("whole", "Неизвестная стоимость")} рублей'

        departure_platform = train.get("departure_platform", "")
        if not departure_platform:
            departure_platform = "неизвестного пути"

        train_info.append(
            f'{emoji} <b>{train["thread"]["number"]} | {train["thread"]["title"]}</b>\n'
            f'<i>Отправляется с {departure_platform} в {dep.hour}:{dep.minute:02d}</i>\n'
            f'<i>С остановками: {train.get("stops", "Неизвестно")}</i>\n'
            f'<i>Стоимость билета: {ticket_price}</i>\n'
            f'<i>{transport_subtype} | {train["thread"]["carrier"]["title"]}</i>\n'
        )

        count += 1
        if count >= 3:
            break

    if train_info:
        return f"📋 <b>Расписание поездов от \"{from_title}\" до \"{to_title}\" на {formatted_date} по {tomorrow_date}</b>\n\n" + "\n".join(
            train_info)
    else:
        return None

async def update_trains(message: Message, user_id: int):
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
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(
                    text="🚫 | Отменить автообновление", callback_data=f"cancel_update_{user_id}")]])

            else:
                additional_text = f"\n<b>🚆⌛ Автообновление было завершено в {current_time}, учтите актуальность данного расписания!</b>"
                auto_update_users[user_id] = False
                keyboard = None

            train_info += additional_text
            media = InputMediaPhoto(media=random_image, caption=train_info, parse_mode='HTML')
            await message.edit_media(media, reply_markup=keyboard)
        else:
            await message.edit_text(
                "🚆🚫 <b>На текущий момент, на данную дату или заданному маршруту мы не нашли расписание. "
                "Пожалуйста, укажите текущую или же дальнейшую дату для расписания и проверьте, правильно ли вы указали названия станций для маршрута.</b>",
                parse_mode='HTML')
        await asyncio.sleep(60)


@dp.message(CommandStart())
async def send_welcome(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅ | Указать маршрут", callback_data="find_route"),
                          InlineKeyboardButton(text="🚆 | Узнать расписание электричек", callback_data="send_suburban")]])

    random_image = random.choice(image_urls)
    await message.answer_photo(photo=random_image, caption="📋 <b>Расписание пригородных электричек и экспрессов</b>\n\n"
                                       "Данный бот позволяет вам быстро узнать расписание об вашем поезде. Для этого нужно лишь указать откуда и куда вам надо приехать и появиться полная информация об ближайших пригородных электричек и поездах.\n\n"
                                       "Для того, чтобы изменить или узнать расписание по текущим указаниям маршрута, нажмите кнопки ниже.",
                               parse_mode='HTML', reply_markup=keyboard)


# @dp.message_handler(commands=['route'])
# async def find_trains(message: types.Message):
#     global auto_update_users, current_messages
#     user_id = message.from_user.id
#
#     if auto_update_users.get(user_id, False):
#         await message.reply("🚆📋 <b>На текущий момент вы не можете изменить маршрут, т.к. активно расписание с автообновление на данный момент. Пожалуйста, отключите текущее автообновление перед запуском нового расписания.</b>", parse_mode='HTML')
#         return
#
#     initial_message = await message.reply("🚆📋 <b>Получаем расписание поездов...</b>", parse_mode='HTML')
#     await update_trains(initial_message, user_id)


async def send_trains(message: Message):
    global auto_update_users, current_messages
    user_id = message.from_user.id

    if auto_update_users.get(user_id, False):
        await message.reply("🚆📋 <b>Расписание с автообновление на данный момент активно."
                            "Пожалуйста, отключите текущее автообновление перед запуском нового расписания.</b>", parse_mode='HTML')
        return
    initial_message = await message.reply("🚆📋 <b>Получаем расписание поездов...</b>", parse_mode='HTML')
    await update_trains(initial_message, user_id)


@dp.callback_query(lambda c: c.data.startswith('cancel_update_'))
async def cancel_update(callback_query: types.CallbackQuery):
    global auto_update_users
    user_id = int(callback_query.data.split('_')[-1])
    auto_update_users[user_id] = False
    await bot.answer_callback_query(callback_query.id, text="🚫⌛ Автообновление было отменено, учтите что данные могут быть неактуальными. Отмена произойдет в течении минуты.")
    await bot.edit_message_reply_markup(callback_query.message.business_connection_id, callback_query.message.chat.id, callback_query.message.message_id,
                                        reply_markup=None)


@dp.callback_query(lambda c: c.data == "send_suburban")
async def handle_send_suburban(callback_query: types.CallbackQuery):
    await send_trains(callback_query.message)


# async def on_shutdown():
#     global current_messages
#     for user_id, message in current_messages.items():
#         current_time = datetime.now().strftime('%H:%M')
#         await bot.send_message(message.chat.id, f"\n🚆🚫 <b>Бот остановил свою работу. "
#                                f"Это связано с техническими работами и ошибками. "
#                                f"Последнее автообновление вашего расписания было в {current_time}. "
#                                f"Будьте внимательны и следите за расписанием!</b>",
#                                parse_mode='HTML')
#     await dp.storage.close()


if __name__ == '__main__':
    bot = Bot(token=token_bot)
    asyncio.run(dp.start_polling(bot))

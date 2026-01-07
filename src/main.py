import asyncio
import logging
import os
import random

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.mongo import MongoStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from aiogram.client.default import DefaultBotProperties

from src.commands.debug import debug
from src.commands.feedback import feedback
from src.commands.schedule import schedule
from src.commands.scooters import scooters
from src.commands.support_telegram_stars import support
from src.route_select.route_selector import route_selector
from src.troika_interaction.lk_troika import troika_lk
from src.troika_interaction.payments_troika import troika_pay
from src.troika_interaction.authorization_troika import troika_auth
from src.commands.transport_card import transport_card
from src.utils.load_config import load_config

load_dotenv()

admin_id = os.getenv('ADMIN_ID')

dp = Dispatcher(storage=MongoStorage(client=AsyncIOMotorClient()).from_url(
    os.getenv("MONGO_URL")))
dp.include_router(route_selector)
dp.include_router(troika_pay)
dp.include_router(troika_auth)
dp.include_router(troika_lk)

dp.include_router(transport_card)
dp.include_router(support)
dp.include_router(debug)
dp.include_router(feedback)
dp.include_router(schedule)
dp.include_router(scooters)

config = load_config()
suburban_urls = config.suburban_urls
russian_timezones = config.russian_timezones

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%d-%m-%y %H:%M:%S')


@dp.message(CommandStart())
async def send_welcome(message: Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🧭 | Установить маршрут", callback_data="routes"),
                          InlineKeyboardButton(text="⚙ | Настройки", callback_data="settings")],
                         [InlineKeyboardButton(text="📨 | Обратная связь", callback_data="feedback")],
                         [InlineKeyboardButton(text="↕ | Поиск по маршруту следования",
                                               callback_data="schedule_route")],
                         [InlineKeyboardButton(text="⭐ | Поддержать разработчика", callback_data="support_developer")]])

    random_image = random.choice(suburban_urls)
    await message.answer_photo(photo=random_image,
                               caption="🗓 <b>Расписание железнодорожного транспорта</b>\n\n"
                                       "Данный бот позволяет вам быстро узнать расписание об вашем пригородном поезде или поездах дальнего следования. Для этого нужно лишь указать ОТКУДА и КУДА вам надо поехать и появиться полная информация об ближайших пригородных поездов и поездах дальнего следования.\n\n"
                                       "Для того, чтобы изменить маршрут следования или узнать расписание по текущему маршруту следования, нажмите кнопки ниже, либо воспользуйтесь командами /suburban, /train и /route.\n\n"
                                       "Если у вас есть предложение или вы нашли баги и ошибки в ответе бота, вы можете связаться с нами при помощи команды /feedback.\n\n"
                                       "Также для корректно работы бота, НЕОБХОДИМО выбрать свой часовой пояс, чтобы расписание отображалось корректно вашем регионе. Это можно сделать в настройках бота.",
                               reply_markup=keyboard)
    await state.set_state()

    try:
        await message.delete()
    except Exception:
        pass


# Schedule and route
@dp.message(Command('route'))
async def send_routes(message: Message, state: FSMContext):
    data = await state.get_data()
    tz = data.get('timezone', 'Europe/Moscow')

    if tz == 'Europe/Moscow':
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🏫 | Станции", callback_data="find_route"),
                              InlineKeyboardButton(text="🏙 | Города", callback_data="find_route_city")],
                             [InlineKeyboardButton(text="🚇 | Московский метрополитен",
                                                   callback_data="find_underground_route")]])
    else:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🏫 | Станции", callback_data="find_route"),
                              InlineKeyboardButton(text="🏙 | Города", callback_data="find_route_city")]])
    await message.reply("🧭🔍 <b>Выберите, какой тип маршрута следования вам необходимо установить.</b>",
                        reply_markup=keyboard)
    await state.set_state()

    try:
        await message.delete()
    except Exception:
        pass


@dp.callback_query(lambda c: c.data == "schedule_route")
async def handle_schedule(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tz = data.get('timezone', 'Europe/Moscow')

    if tz == 'Europe/Moscow':
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🚉 | Пригородные поезда", callback_data="send_suburban"),
                              InlineKeyboardButton(text="🚂 | Междугородние поезда", callback_data="send_train")],
                             [InlineKeyboardButton(text="✈ | Самолёты", callback_data="send_plane"),
                              InlineKeyboardButton(text="🚐 | Междугородние автобусы",
                                                   callback_data="send_intercity_bus")],
                             [InlineKeyboardButton(text="🚇 | Московский метрополитен",
                                                   callback_data="send_underground")],
                             [InlineKeyboardButton(text="🚊 | Московский транспорт",
                                                   callback_data="send_tramway")]
                             ])
    else:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🚉 | Пригородные поезда", callback_data="send_suburban"),
                              InlineKeyboardButton(text="🚂 | Междугородние поезда", callback_data="send_train")],
                             [InlineKeyboardButton(text="✈ | Самолёты", callback_data="send_plane")],
                             InlineKeyboardButton(text="🚐 | Междугородние автобусы",
                                                  callback_data="send_intercity_bus")])
    await callback_query.message.reply("🗓🔍 <b>Выберите какой тип транспорта вам необходимо узнать расписание.</b>",
                                       reply_markup=keyboard)


@dp.callback_query(lambda c: c.data == "routes")
async def handle_routes(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tz = data.get('timezone', 'Europe/Moscow')

    if tz == 'Europe/Moscow':
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🏫 | Станции", callback_data="find_route"),
                              InlineKeyboardButton(text="🏙 | Города", callback_data="find_route_city")],
                             [InlineKeyboardButton(text="🚇 | Московский метрополитен",
                                                   callback_data="find_underground_route")]])
    else:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🏫 | Станции", callback_data="find_route"),
                              InlineKeyboardButton(text="🏙 | Города", callback_data="find_route_city")]])
    await callback_query.message.reply(
        "🧭🔍 <b>Выберите какой тип маршрут следования вам необходимо установить.</b>",
        reply_markup=keyboard)


@dp.callback_query(lambda c: c.data == 'delete_message')
async def delete_message(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
    await state.set_state(None)
    # await bot.answer_callback_query(callback_query.id, text="🗑 Расписание было удалено.")


# Settings
@dp.callback_query(lambda c: c.data == "settings")
async def handle_settings(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    express_type = data.get('express_type', False)
    express_text = "🚅 | Только экспрессы" if express_type else "🚆 | Обычные и экспрессы"
    settings_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚮 | Очистка маршрутов", callback_data="clear_route")],
            [InlineKeyboardButton(text="🔁 | Инверсия маршрута", callback_data="inversion_route")],
            [InlineKeyboardButton(text="🕒 | Часовой пояс", callback_data="select_timezone")],
            [InlineKeyboardButton(text=express_text, callback_data="toggle_express_type")],
            [InlineKeyboardButton(text="⬅ | Назад", callback_data="back")]
        ])
    await bot.edit_message_reply_markup(chat_id=callback_query.message.chat.id,
                                        message_id=callback_query.message.message_id,
                                        reply_markup=settings_keyboard)


@dp.callback_query(lambda c: c.data == "toggle_express_type")
async def handle_toggle_express_type(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    express_type = data.get('express_type', False)
    new_express_type = not express_type
    await state.update_data(express_type=new_express_type)

    express_text = "🚅 | Только экспрессы" if new_express_type else "🚆 | Обычные и экспрессы"

    settings_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚮 | Очистка маршрутов", callback_data="clear_route")],
            [InlineKeyboardButton(text="🔁 | Инверсия маршрута", callback_data="inversion_route")],
            [InlineKeyboardButton(text="🕒 | Часовой пояс", callback_data="select_timezone")],
            [InlineKeyboardButton(text=express_text, callback_data="toggle_express_type")],
            [InlineKeyboardButton(text="⬅ | Назад", callback_data="back")]
        ])
    await bot.edit_message_reply_markup(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=settings_keyboard
    )


@dp.callback_query(lambda c: c.data == "back")
async def handle_back(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🧭 | Установить маршрут", callback_data="routes"),
                          InlineKeyboardButton(text="⚙ | Настройки", callback_data="settings")],
                         [InlineKeyboardButton(text="📨 | Обратная связь", callback_data="feedback")],
                         [InlineKeyboardButton(text="↕ | Поиск по маршруту следования",
                                               callback_data="schedule_route")],
                         [InlineKeyboardButton(text="⭐ | Поддержать разработчика", callback_data="support_developer")]])
    await bot.edit_message_reply_markup(chat_id=callback_query.message.chat.id,
                                        message_id=callback_query.message.message_id,
                                        reply_markup=keyboard)


# Timezone
@dp.callback_query(lambda c: c.data == 'select_timezone')
async def select_timezone(callback_query: types.CallbackQuery):
    timezone_buttons = [
        [InlineKeyboardButton(text=f"🗺 | {label}", callback_data=f'set_timezone_{tz}')] for tz, label in
        russian_timezones.items()
    ]
    timezone_keyboard = InlineKeyboardMarkup(inline_keyboard=timezone_buttons)
    await callback_query.message.edit_reply_markup(reply_markup=timezone_keyboard)


@dp.callback_query(lambda c: c.data.startswith('set_timezone_'))
async def set_timezone(callback_query: types.CallbackQuery, state: FSMContext):
    selected_timezone = callback_query.data.split('_')[-1]
    label = russian_timezones[selected_timezone]
    await state.update_data(timezone=selected_timezone)
    await callback_query.answer(f"🕒 Часовой пояс установлен на {label}.")
    await handle_settings(callback_query, state)


# Clear routes
@dp.callback_query(lambda c: c.data == "clear_route")
async def clear_route(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tz = data.get('timezone', 'Europe/Moscow')

    if tz == 'Europe/Moscow':
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🏫 | Станции", callback_data="clear_route_station"),
                              InlineKeyboardButton(text="🏙 | Города", callback_data="clear_route_city")],
                             [InlineKeyboardButton(text="🚇 | Московский метрополитен",
                                                   callback_data="clear_route_underground")]])
    else:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🏫 | Станции", callback_data="clear_route_station"),
                              InlineKeyboardButton(text="🏙 | Города", callback_data="clear_route_city")]])

    await bot.send_message(callback_query.message.chat.id,
                           "🛤🚮 <b>Выберете тип маршрута следования, которые вы хотите желаете очистить.</b>",
                           reply_markup=keyboard)


@dp.callback_query(lambda c: c.data in ["clear_route_station", "clear_route_city", "clear_route_underground"])
async def clear_route_selection(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data == "clear_route_station":
        await state.update_data(from_station=None, to_station=None)
        response_message = "🚆🚮 <b>Маршруты следования станций были успешно очищены. Для того, чтобы установить новый маршрут следования воспользуйтесь командой /route.</b>"
    elif callback_query.data == "clear_route_underground":
        await state.update_data(from_station_underground=None, to_station_underground=None)
        response_message = "🚇🚮 <b>Маршруты следования станций московского метрополитена были успешно очищены. Для того, чтобы установить новый маршрут следования воспользуйтесь командой /route.</b>"
    elif callback_query.data == "clear_route_city":
        await state.update_data(from_city=None, to_city=None)
        response_message = "🚂🚮 <b>Маршруты следования городов были успешно очищены. Для того, чтобы установить новый маршрут следования воспользуйтесь командой /route.</b>"
    await bot.edit_message_text(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id,
                                text=response_message)


# Inversion routes
@dp.callback_query(lambda c: c.data == "inversion_route")
async def inversion_route(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tz = data.get('timezone', 'Europe/Moscow')

    if tz == 'Europe/Moscow':
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🏫 | Станции", callback_data="inversion_route_station"),
                              InlineKeyboardButton(text="🏙 | Города", callback_data="inversion_route_city")],
                             [InlineKeyboardButton(text="🚇 | Московский метрополитен",
                                                   callback_data="inversion_route_underground")]])
    else:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🏫 | Станции", callback_data="inversion_route_station"),
                              InlineKeyboardButton(text="🏙 | Города", callback_data="inversion_route_city")]])

    await bot.send_message(callback_query.message.chat.id,
                           "📅🔁 <b>Выберете какой тип маршрут следования вам необходимо поменять местами.</b>",
                           reply_markup=keyboard)


@dp.callback_query(
    lambda c: c.data in ["inversion_route_station", "inversion_route_city", "inversion_route_underground"])
async def inversion_route_selection(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()

    if callback_query.data == "inversion_route_station":
        from_location = data.get('from_station')
        to_location = data.get('to_station')
        callback_data = "send_suburban"
        message_prefix = "пригородных поездов"
        button_message = "Расписание " + message_prefix
        button_emoji = "🗓"
        emoji = "🚆"
        state_fields = ("station", "station")
    elif callback_query.data == "inversion_route_city":
        from_location = data.get('from_city')
        to_location = data.get('to_city')
        callback_data = "send_train"
        message_prefix = "междугородних поездов"
        button_message = "Расписание " + message_prefix
        button_emoji = "🗓"
        emoji = "🚂"
        state_fields = ("city", "city")
    elif callback_query.data == "inversion_route_underground":
        from_location = data.get('from_station_underground')
        to_location = data.get('to_station_underground')
        callback_data = "send_underground"
        message_prefix = "московского метрополитена"
        button_message = "Построить путь"
        button_emoji = "↕"
        emoji = "🚇"
        state_fields = ("station_underground", "station_underground")

    if from_location and to_location:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=f"{button_emoji} | {button_message}", callback_data=callback_data)]])
        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text=f"{emoji}🔁 <b>Была совершена инверсия маршрута следования для {message_prefix}. Бывшая конечная точка маршрута, стала начальной, а начальная точка — конечной.</b>",
            reply_markup=keyboard
        )
        await state.update_data(**{
            f'from_{state_fields[0]}': to_location,
            f'to_{state_fields[1]}': from_location
        })
    else:
        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text=f"❌🔁 <b>Маршрут следования не был установлен для {message_prefix}. Пожалуйста, установите маршрут перед инверсией маршрута.</b>"
        )


if __name__ == '__main__':
    bot = Bot(token=os.getenv('TOKEN_BOT'), default=DefaultBotProperties(parse_mode='HTML'))
    asyncio.run(dp.start_polling(bot))

import asyncio
import locale
import logging
import os
import random

from aiogram.fsm.state import StatesGroup, State
from pytz import timezone
from datetime import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.mongo import MongoStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, Message, CallbackQuery
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from aiogram.types.input_file import FSInputFile

from src.get_suburban_info import get_suburban_info
from src.get_train_info import get_train_info
from src.utils.load_config import load_config
from src.route_select.route_selector import route_selector

load_dotenv()
locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

token_yandex = os.getenv('TOKEN_YANDEX')
token_bot = os.getenv('TOKEN_BOT')

config = load_config()
train_urls = config.train_urls
suburban_urls = config.suburban_urls
admin_id = os.getenv('ADMIN_ID')
russian_timezones = config.russian_timezones
dp = Dispatcher(storage=MongoStorage(client=AsyncIOMotorClient()).from_url(
    os.getenv("MONGO_URL")))
dp.include_router(route_selector)


class FeedbackStates(StatesGroup):
    awaiting_feedback = State()
    awaiting_reply_text = State()


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%d-%m-%y %H:%M:%S')
auto_update_users = {}


@dp.message(CommandStart())
async def send_welcome(message: Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🧭 | Установить маршрут", callback_data="routes"),
                          InlineKeyboardButton(text="⚙ | Настройки", callback_data="settings")],
                         [InlineKeyboardButton(text="📨 | Обратная связь", callback_data="feedback")],
                         [InlineKeyboardButton(text="↕ | Поиск по маршруту следования",
                                               callback_data="schedule_route")]])

    random_image = random.choice(suburban_urls)
    await message.answer_photo(photo=random_image,
                               caption="🗓 <b>Расписание железнодорожного транспорта</b>\n\n"
                                       "Данный бот позволяет вам быстро узнать расписание об вашем пригородном поезде или поездах дальнего следования. Для этого нужно лишь указать ОТКУДА и КУДА вам надо поехать и появиться полная информация об ближайших пригородных поездов и поездах дальнего следования.\n\n"
                                       "Для того, чтобы изменить маршрут следования или узнать расписание по текущему маршруту следования, нажмите кнопки ниже, либо воспользуйтесь командами /suburban, /train и /route.\n\n"
                                       "Также для корректно работы бота, НЕОБХОДИМО выбрать свой часовой пояс, чтобы расписание отображалось корректно вашем регионе. Это можно сделать в настройках бота.",
                               parse_mode='HTML', reply_markup=keyboard)
    await state.set_state()


# Suburbans
async def update_suburbans(message: Message, user_id: int, state: FSMContext):
    remaining_time = 60
    data = await state.get_data()
    tz = timezone(data.get('timezone', 'Europe/Moscow'))

    from_station = data.get('from_station')
    to_station = data.get('to_station')

    auto_update_users[user_id] = True

    for i in range(60):
        current_time = datetime.now(tz).strftime('%H:%M')
        train_info = get_suburban_info(from_station, to_station, str(tz))
        random_image = random.choice(suburban_urls)

        if not auto_update_users[user_id]:
            train_info += f"\n🚉🚫<b> Автообновление было отменено. Последние данные были обновлены в {current_time}.</b>"
            media = InputMediaPhoto(media=random_image, caption=train_info, parse_mode='HTML')
            await message.edit_media(media)
            auto_update_users[user_id] = False
            return

        if train_info:
            if data.get('enable_auto_update'):
                if i < 59:
                    remaining_time -= 1
                    additional_text = f"\n🚉⌛ <b>Следующее обновление через 1 минуту. Оставшееся время обновления: {remaining_time} минут.</b>"
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🚫 | Отменить автообновление", callback_data="cancel_update")]
                    ])
                else:
                    additional_text = f"\n🚉⌛️ <b>Автообновление было завершено в {current_time}, учтите актуальность данного расписания.</b>"
                    auto_update_users[user_id] = False
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🗑 | Удалить расписание", callback_data="delete_schedule")]
                    ])

                train_info += additional_text
                media = InputMediaPhoto(media=random_image, caption=train_info, parse_mode='HTML')
                await message.edit_media(media, reply_markup=keyboard)
            else:
                additional_text = f"\n🚉 <b>Расписание было вызвано в {current_time} без автообновления, учтите актуальность данного расписания.</b>"
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🗑 | Удалить расписание", callback_data="delete_schedule")]
                ])

                train_info += additional_text
                media = InputMediaPhoto(media=random_image, caption=train_info, parse_mode='HTML')
                await message.edit_media(media, reply_markup=keyboard)
                auto_update_users[user_id] = False
                return
            await asyncio.sleep(60)
        else:
            await message.edit_text(
                "🚆🚫 <b>К сожалению, по вашему маршруту следования мы не нашли расписание. "
                "Пожалуйста, укажите действительный маршрут следования пригородного поезда.</b>",
                parse_mode='HTML')
            auto_update_users[user_id] = False
            return


@dp.callback_query(lambda c: c.data == "send_suburban")
async def handle_send_suburban(callback_query: types.CallbackQuery, state: FSMContext):
    await send_suburbans(callback_query.message, state)
    await callback_query.message.delete()


@dp.message(Command('suburban'))
async def send_suburbans(message: Message, state: FSMContext):
    data = await state.get_data()
    from_station = data.get('from_station')
    to_station = data.get('to_station')
    user_id = message.chat.id

    if auto_update_users.get(user_id, False):
        await message.reply("🚆🗓 <b>Расписание с автообновление на данный момент активно. "
                            "Пожалуйста, отключите текущее автообновление перед запуском нового расписания.</b>",
                            parse_mode='HTML')
        return

    if not from_station or not to_station:
        await message.reply("🚆🏫 <b>Маршрут следования не был установлен. "
                            "Пожалуйста, установите маршрут перед поиском расписания следования пригородных поездов.</b>",
                            parse_mode='HTML')
        return
    else:
        initial_message = await message.reply("🚆🗓 <b>Получаем расписание пригородных поездов...</b>", parse_mode='HTML')
        await update_suburbans(initial_message, user_id, state)
    await state.set_state()


# Trains
async def update_trains(message: Message, user_id: int, state: FSMContext):
    remaining_time = 60
    data = await state.get_data()
    tz = timezone(data.get('timezone', 'Europe/Moscow'))

    from_city = data.get('from_city')
    to_city = data.get('to_city')

    auto_update_users[user_id] = True

    for i in range(60):
        current_time = datetime.now(tz).strftime('%H:%M')
        train_info = get_train_info(from_city, to_city, str(tz))
        random_image = random.choice(train_urls)

        if not auto_update_users[user_id]:
            train_info += f"\n🛤🚫<b> Автообновление было отменено. Последние данные были обновлены в {current_time}.</b>"
            media = InputMediaPhoto(media=random_image, caption=train_info, parse_mode='HTML')
            await message.edit_media(media)
            auto_update_users[user_id] = False
            return

        if train_info:
            if data.get('enable_auto_update'):
                if i < 59:
                    remaining_time -= 1
                    additional_text = f"\n🛤⌛ <b>Следующее обновление через 1 минуту. Оставшееся время обновления: {remaining_time} минут.</b>"
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🚫 | Отменить автообновление", callback_data="cancel_update")]
                    ])
                else:
                    additional_text = f"\n🛤⌛ <b>Автообновление было завершено в {current_time}, учтите актуальность данного расписания.</b>"
                    auto_update_users[user_id] = False
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🗑 | Удалить расписание", callback_data="delete_schedule")]
                    ])

                train_info += additional_text
                media = InputMediaPhoto(media=random_image, caption=train_info, parse_mode='HTML')
                await message.edit_media(media, reply_markup=keyboard)
            else:
                additional_text = f"\n🛤 <b>Расписание было вызвано в {current_time} без автообновления, учтите актуальность данного расписания.</b>"
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🗑 | Удалить расписание", callback_data="delete_schedule")]
                ])

                train_info += additional_text
                media = InputMediaPhoto(media=random_image, caption=train_info, parse_mode='HTML')
                await message.edit_media(media, reply_markup=keyboard)
                auto_update_users[user_id] = False
                return
            await asyncio.sleep(60)
        else:
            await message.edit_text(
                "🚂🚫 <b>К сожалению, по вашему маршруту следования мы не нашли расписание. "
                "Пожалуйста, укажите действительный маршрут следования поезда дальнего следования.</b>",
                parse_mode='HTML')
            auto_update_users[user_id] = False
            return


@dp.message(Command('train'))
async def send_trains(message: Message, state: FSMContext):
    data = await state.get_data()
    from_city = data.get('from_city')
    to_city = data.get('to_city')
    user_id = message.chat.id

    if auto_update_users.get(user_id, False):
        await message.reply("🚂🗓 <b>Расписание с автообновление на данный момент активно. "
                            "Пожалуйста, отключите текущее автообновление перед запуском нового расписания.</b>",
                            parse_mode='HTML')
        return

    if not from_city or not to_city:
        await message.reply("🚂🏙 <b>Маршрут следования не был установлен. "
                            "Пожалуйста, установите маршрут перед поиском расписания следования электричек.</b>",
                            parse_mode='HTML')
        return
    else:
        initial_message = await message.reply("🚂🗓 <b>Получаем расписание поездов дальнего следования...</b>",
                                              parse_mode='HTML')
        await update_trains(initial_message, user_id, state)
    await state.set_state()


@dp.callback_query(lambda c: c.data == "send_train")
async def handle_send_train(callback_query: types.CallbackQuery, state: FSMContext):
    await send_trains(callback_query.message, state)
    await callback_query.message.delete()


# Schedule and route
@dp.message(Command('route'))
async def send_routes(message: Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🏫 | Станции", callback_data="find_route"),
                          InlineKeyboardButton(text="🏙 | Города", callback_data="find_route_city")]])
    await message.reply("🧭🔍 <b>Выберите, какой тип маршрута следования для расписания вам необходимо установить.</b>",
                        parse_mode='HTML', reply_markup=keyboard)
    await state.set_state()


@dp.callback_query(lambda c: c.data == "schedule_route")
async def handle_schedule(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🚉 | Пригородные поезда", callback_data="send_suburban"),
                          InlineKeyboardButton(text="🚂 | Поезда дальнего следования", callback_data="send_train")]])
    await callback_query.message.reply("🗓🔍 <b>Выберите какой тип расписание транспорта вам необходимо узнать.</b>",
                                       parse_mode='HTML', reply_markup=keyboard)


@dp.callback_query(lambda c: c.data == "routes")
async def handle_routes(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🏫 | Станции", callback_data="find_route"),
                          InlineKeyboardButton(text="🏙 | Города", callback_data="find_route_city")]])
    await callback_query.message.reply(
        "🧭🔍 <b>Выберите какой тип маршрут следования для расписания вам необходимо установить.</b>", parse_mode='HTML',
        reply_markup=keyboard)


@dp.callback_query(lambda c: c.data == 'delete_schedule')
async def delete_schedule(callback_query: types.CallbackQuery):
    await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
    await bot.answer_callback_query(callback_query.id, text="🗑 Расписание было удалено.")


@dp.callback_query(lambda c: c.data == 'cancel_update')
async def cancel_update(callback_query: types.CallbackQuery):
    user_id = callback_query.message.chat.id
    auto_update_users[user_id] = False
    await bot.answer_callback_query(callback_query.id,
                                    text="🚫⌛ Автообновление было отменено, учтите что данные могут быть неактуальными. Отмена произойдет в течении минуты.")
    await bot.edit_message_reply_markup(callback_query.message.business_connection_id, callback_query.message.chat.id,
                                        callback_query.message.message_id,
                                        reply_markup=None)


# Settings
@dp.callback_query(lambda c: c.data == "enable_auto_update")
async def handle_enable_auto_update(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    enable_auto_update = data.get('enable_auto_update', False)
    new_status = not enable_auto_update
    await state.update_data(enable_auto_update=new_status)

    emoji = "✅" if new_status else "❌"
    settings_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{emoji} | Автообновление", callback_data="enable_auto_update"),
             InlineKeyboardButton(text="🚮 | Очистка маршрутов", callback_data="clear_route")],
            [InlineKeyboardButton(text="🔁 | Инверсия маршрута", callback_data="inversion_route")],
            [InlineKeyboardButton(text="🕒 | Часовой пояс", callback_data="select_timezone")],
            [InlineKeyboardButton(text="⬅ | Назад", callback_data="back")]
        ])
    await bot.edit_message_reply_markup(chat_id=callback_query.message.chat.id,
                                        message_id=callback_query.message.message_id,
                                        reply_markup=settings_keyboard)


@dp.callback_query(lambda c: c.data == "settings")
async def handle_settings(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    enable_auto_update = data.get('enable_auto_update', False)
    emoji = "✅" if enable_auto_update else "❌"
    settings_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{emoji} | Автообновление", callback_data="enable_auto_update"),
             InlineKeyboardButton(text="🚮 | Очистка маршрутов", callback_data="clear_route")],
            [InlineKeyboardButton(text="🔁 | Инверсия маршрута", callback_data="inversion_route")],
            [InlineKeyboardButton(text="🕒 | Часовой пояс", callback_data="select_timezone")],
            [InlineKeyboardButton(text="⬅ | Назад", callback_data="back")]
        ])
    await bot.edit_message_reply_markup(chat_id=callback_query.message.chat.id,
                                        message_id=callback_query.message.message_id,
                                        reply_markup=settings_keyboard)


@dp.callback_query(lambda c: c.data == "back")
async def handle_back(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🧭 | Установить маршрут", callback_data="routes"),
                          InlineKeyboardButton(text="⚙ | Настройки", callback_data="settings")],
                         [InlineKeyboardButton(text="📨 | Обратная связь", callback_data="feedback")],
                         [InlineKeyboardButton(text="↕ | Поиск по маршруту следования",
                                               callback_data="schedule_route")]])
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
async def clear_route(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🏫 | Станции", callback_data="clear_route_station"),
                          InlineKeyboardButton(text="🏙 | Города", callback_data="clear_route_city")]])
    await bot.send_message(callback_query.message.chat.id,
                           "🛤🚮 <b>Выберете тип маршрута следования, которые вы хотите желаете очистить.</b>",
                           parse_mode='HTML', reply_markup=keyboard)


@dp.callback_query(lambda c: c.data in ["clear_route_station", "clear_route_city"])
async def clear_route_selection(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data == "clear_route_station":
        await state.update_data(from_station=None, to_station=None, from_station_title=None, to_station_title=None)
        response_message = "🚆🚮 <b>Маршруты следования станций были успешно очищены. Для того, чтобы установить новый маршрут следования воспользуйтесь командой /route.</b>"
    else:
        await state.update_data(from_city=None, to_city=None, from_city_title=None, to_city_title=None)
        response_message = "🚂🚮 <b>Маршруты следования городов были успешно очищены. Для того, чтобы установить новый маршрут следования воспользуйтесь командой /route.</b>"
    await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
    await bot.send_message(callback_query.message.chat.id, response_message, parse_mode='HTML')


# Inversion routes
@dp.callback_query(lambda c: c.data == "inversion_route")
async def inversion_route(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🏫 | Станции", callback_data="inversion_route_station"),
                          InlineKeyboardButton(text="🏙 | Города", callback_data="inversion_route_city")]])
    await bot.send_message(callback_query.message.chat.id,
                           "📅🔁 <b>Выберете какой тип маршрут следования вам необходимо поменять местами.</b>",
                           parse_mode='HTML', reply_markup=keyboard)


@dp.callback_query(lambda c: c.data in ["inversion_route_station", "inversion_route_city"])
async def inversion_route_selection(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()

    if callback_query.data == "inversion_route_station":
        from_location = data.get('from_station')
        to_location = data.get('to_station')
        from_title = data.get('from_station_title')
        to_title = data.get('to_station_title')
        callback_data = "send_suburban"
        message_prefix = "пригородных поездов"
        emoji = "🚆"
    else:
        from_location = data.get('from_city')
        to_location = data.get('to_city')
        from_title = data.get('from_city_title')
        to_title = data.get('to_city_title')
        callback_data = "send_train"
        message_prefix = "поездов дальнего следования"
        emoji = "🚂"

    if from_location and to_location:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=f"{emoji} | Расписание {message_prefix}", callback_data=callback_data)]])
        await bot.send_message(callback_query.message.chat.id,
                               f"{emoji}🔁 <b>Была совершена инверсия маршрута следования для {message_prefix}. {to_title} является отправной точкой и {from_title} является конечной точкой.</b>",
                               parse_mode='HTML', reply_markup=keyboard)
        await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
        await state.update_data(
            **{f'from_{("station" if callback_data == "send_suburban" else "city")}': to_location,
               f'to_{("station" if callback_data == "send_suburban" else "city")}': from_location,
               f'from_{("station_title" if callback_data == "send_suburban" else "city_title")}': to_title,
               f'to_{("station_title" if callback_data == "send_suburban" else "city_title")}': from_title}
        )
    else:
        await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
        await bot.send_message(callback_query.message.chat.id,
                               f"❌🔁 <b>Маршрут следования не был установлен для {message_prefix}. Пожалуйста, установите маршрут перед инверсией маршрута.</b>",
                               parse_mode='HTML')


# Debug
@dp.message(Command('feedback'))
@dp.callback_query(lambda c: c.data == 'feedback')
async def feedback_command(event, state: FSMContext):
    user_state = await state.get_data()

    if user_state.get('feedback_in_progress'):
        if isinstance(event, Message):
            await event.answer(
                "ℹ✉ <b>У вас уже есть одно открытое обращение. Пожалуйста, дождитесь ответа. Если вам уже ответили на обращение, то отметьте его прочитанным, перед тем, как написать следующее.</b>",
                parse_mode='HTML')
        elif isinstance(event, CallbackQuery):
            await event.message.answer(
                "ℹ✉ <b>У вас уже есть одно открытое обращение. Пожалуйста, дождитесь ответа. Если вам уже ответили на обращение, то отметьте его прочитанным, перед тем, как написать следующее.</b>",
                parse_mode='HTML')
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отменить обращение", callback_data="cancel_feedback")]
        ])

    if isinstance(event, Message):
        await event.answer(
            "📨 <b>Пожалуйста, напишите ваше сообщение, которое будет передано создателю бота. \n\n</b>"
            "В своем сообщении вы можете рассказать об пожеланиях, обнаруженных ошибках и багах, оставить отзыв по поводу использования бота. "
            "Убедительная просьба, не писать в обратную связь всякий не связанный бред, имейте уважение.",
            parse_mode='HTML', reply_markup=keyboard)
    elif isinstance(event, CallbackQuery):
        await event.message.answer(
            "📨 <b>Пожалуйста, напишите ваше сообщение, которое будет передано создателю бота. \n\n</b>"
            "В своем сообщении вы можете рассказать об пожеланиях, обнаруженных ошибках и багах, оставить отзыв по поводу использования бота. "
            "Убедительная просьба, не писать в обратную связь всякий не связанный бред, имейте уважение.",
            parse_mode='HTML', reply_markup=keyboard)

    await state.set_state(FeedbackStates.awaiting_feedback)


@dp.message(FeedbackStates.awaiting_feedback)
async def handle_feedback(message: Message, state: FSMContext):
    feedback_text = message.text
    user = message.from_user
    feedback_message = (
        f"💌 <b>У вас появилось новое обращение от {user.full_name} (@{user.username}):</b>\n\n{feedback_text}\n\n"
        f"<b>Для ответа пользователю используйте кнопку ниже.</b>"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✉️ Ответить пользователю", callback_data=f"reply_{user.id}")]
        ]
    )

    await bot.send_message(chat_id=admin_id, text=feedback_message, parse_mode='HTML', reply_markup=keyboard)
    await message.answer("📧 <b>Спасибо за обратную связь! В течении времени вам ответит создатель бота.</b>",
                         parse_mode='HTML')
    await state.update_data(feedback_in_progress=True)
    await state.set_state()


@dp.callback_query(lambda c: c.data.startswith("reply_"))
async def ask_reply_text(callback_query: CallbackQuery, state: FSMContext):
    if callback_query.message.chat.id != int(admin_id):
        return
    user_id = int(callback_query.data.split("_")[1])
    await state.update_data(reply_user_id=user_id)
    await bot.send_message(chat_id=admin_id, text="📝 <b>Пожалуйста, введите текст ответа пользователю:</b>",
                           parse_mode='HTML')
    await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
    await state.set_state(FeedbackStates.awaiting_reply_text)


@dp.callback_query(lambda c: c.data == 'cancel_feedback')
async def cancel_feedback_reply_text(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_text("❌📧 <b>Вы отменили обратную связь с создателем бота.</b>", parse_mode='HTML')
    await state.update_data(feedback_in_progress=False)
    await state.set_state()


@dp.callback_query(lambda c: c.data == 'read_feedback')
async def read_feedback(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(feedback_in_progress=False)
    await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
    await state.set_state()


@dp.message(FeedbackStates.awaiting_reply_text)
async def send_reply(message: Message, state: FSMContext):
    state_data = await state.get_data()
    user_id = state_data.get("reply_user_id")
    reply_text = message.text

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Пометить прочитанным", callback_data="read_feedback")]
        ]
    )

    try:
        await bot.send_message(chat_id=user_id,
                               text=f"📩 <b>Вам поступило сообщение от создателя бота в ответ на ваше обращение:</b>\n\n{reply_text}",
                               parse_mode='HTML', reply_markup=keyboard)
        await message.answer("📧 <b>Сообщение было успешно отправлено пользователю.</b>", parse_mode='HTML')
    except Exception as e:
        await message.answer(f"❌ <b>Не удалось отправить сообщение пользователю. Ошибка:</b> {e}", parse_mode='HTML')
    await state.set_state()


@dp.message(Command('log'))
async def send_log_file(message: Message, state: FSMContext):
    data = await state.get_data()
    debug_menu = data.get('debug_menu')
    if debug_menu:
        log_file_path = 'YandexRaspBot-error.log'
        if os.path.exists(log_file_path):
            await message.answer_document(FSInputFile(log_file_path),
                                          caption="✅⚙ <b>Файл логов был найден, отправляю его вам! Чтобы снова вызвать и получить логи, также воспользуйтесь командой /log.</b>",
                                          parse_mode='HTML')
        else:
            await message.answer(
                "❌⚙ <b>Файл логов не был найден. Скорее всего его не существует в текущей директории сервера.</b>",
                parse_mode='HTML')
    else:
        await state.update_data(debug_menu=False)


@dp.message(Command('requests_url'))
async def send_requests_url(message: Message, state: FSMContext):
    data = await state.get_data()
    date = datetime.now().strftime('%Y-%m-%d')
    from_city = data.get('from_city')
    to_city = data.get('to_city')

    from_station = data.get('from_station')
    to_station = data.get('to_station')

    tz = timezone(data.get('timezone', 'Europe/Moscow'))

    suburban_url = f"https://api.rasp.yandex.net/v3.0/search?apikey={token_yandex}&from={from_station}&to={to_station}&lang=ru_RU&date={date}&result_timezone={tz}&transport_types=suburban&limit=250"
    train_url = f"https://api.rasp.yandex.net/v3.0/search?apikey={token_yandex}&from={from_city}&to={to_city}&lang=ru_RU&date={date}&result_timezone={tz}&transport_types=train&limit=250"

    debug_menu = data.get('debug_menu')
    if debug_menu:
        await message.answer("✅🔗 <b>Вот ссылки API запросов для тестирования в Postman.\n\n</b>"
                             f"🚆 <b>API запрос пригородных поездов с выбранными вами станциями: {suburban_url}\n\n</b>"
                             f"🚂 <b>API запрос поездов дальнего следования с выбранными вами городами: {train_url}\n\n</b>"
                             "<b>Для просмотра информации из данных API, требуется зайти на https://www.postman.com/ и вставить туда ссылку либо открыть ссылку в браузере.</b>",
                             parse_mode='HTML')
    else:
        await state.update_data(debug_menu=False)


if __name__ == '__main__':
    bot = Bot(token=token_bot)
    asyncio.run(dp.start_polling(bot))

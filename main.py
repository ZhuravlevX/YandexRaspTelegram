import asyncio
import locale
import logging
import os
import random

from aiogram.fsm.state import StatesGroup, State
from pytz import timezone
from datetime import datetime

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.mongo import MongoStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, Message, CallbackQuery, \
    LabeledPrice, PreCheckoutQuery
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from aiogram.types.input_file import FSInputFile
from aiogram.client.default import DefaultBotProperties

from src.request.get_suburban_info import get_suburban_info
from src.request.get_train_info import get_train_info
from src.request.get_underground_info import get_underground_info
from src.utils.load_config import load_config
from src.route_select.route_selector import route_selector
from src.utils.Image_selector import ImageSelector

load_dotenv()
locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

token_yandex = os.getenv('TOKEN_YANDEX')
token_bot = os.getenv('TOKEN_BOT')

config = load_config()
train_urls = config.train_urls
underground_urls = config.underground_urls
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


# Suburbans
async def update_suburbans(message: Message, user_id: int, state: FSMContext):
    remaining_time = 60
    data = await state.get_data()
    tz = timezone(data.get('timezone', 'Europe/Moscow'))

    from_station = data.get('from_station')
    to_station = data.get('to_station')

    express_type = data.get('express_type', False)

    auto_update_users[user_id] = True

    for i in range(60):
        current_time = datetime.now(tz).strftime('%H:%M')
        train_info = get_suburban_info(from_station, to_station, str(tz), express_type)
        suburban_image_selector = ImageSelector(suburban_urls)
        random_image = suburban_image_selector.get_random_image()

        if not auto_update_users[user_id]:
            train_info += f"\n🚉🚫<b> Автообновление было отменено. Последние данные были обновлены в {current_time}.</b>"
            media = InputMediaPhoto(media=random_image, caption=train_info)
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
                media = InputMediaPhoto(media=random_image, caption=train_info)
                await message.edit_media(media, reply_markup=keyboard)
            else:
                additional_text = f"\n🚉 <b>Расписание было вызвано в {current_time} без автообновления, учтите актуальность данного расписания.</b>"
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🗑 | Удалить расписание", callback_data="delete_schedule")]
                ])

                train_info += additional_text
                media = InputMediaPhoto(media=random_image, caption=train_info)
                await message.edit_media(media, reply_markup=keyboard)
                auto_update_users[user_id] = False
                return
            await asyncio.sleep(60)
        else:
            await message.edit_text(
                "🚆🚫 <b>К сожалению, по вашему маршруту следования мы не нашли расписание. "
                "Пожалуйста, укажите действительный маршрут следования пригородного поезда.</b>")
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
                            "Пожалуйста, отключите текущее автообновление перед запуском нового расписания.</b>")
        return

    if not from_station or not to_station:
        await message.reply("🚆🏫 <b>Маршрут следования не был установлен. "
                            "Пожалуйста, установите маршрут перед поиском расписания следования пригородных поездов.</b>")
        return
    else:

        initial_message = await message.reply("🚆🗓 <b>Получаем расписание пригородных поездов...</b>")
        try:
            await message.delete()
        except Exception:
            pass
        await update_suburbans(initial_message, user_id, state)
    await state.set_state()

    try:
        await message.delete()
    except Exception:
        pass


# Undergrounds
async def update_underground(message: Message, user_id: int, state: FSMContext):
    remaining_time = 3600
    data = await state.get_data()

    from_station_underground = data.get('from_station_underground')
    to_station_underground = data.get('to_station_underground')

    auto_update_users[user_id] = True
    last_valid_train_info = None

    for i in range(120):
        current_time = datetime.now().strftime('%H:%M')
        train_info = get_underground_info(from_station_underground, to_station_underground)
        underground_image_selector = ImageSelector(underground_urls)
        random_image = underground_image_selector.get_random_image()

        if not auto_update_users[user_id]:
            train_info = last_valid_train_info or train_info
            train_info += f"\n🚇🚫<b> Автообновление было отменено. Последние данные были обновлены в {current_time}.</b>"
            media = InputMediaPhoto(media=random_image, caption=train_info)
            await message.edit_media(media)
            auto_update_users[user_id] = False
            return

        if not train_info:
            if last_valid_train_info:
                train_info = last_valid_train_info
            else:
                if i == 0:
                    await asyncio.sleep(10)
                    train_info = get_underground_info(from_station_underground, to_station_underground)
                    if not train_info:
                        await message.edit_text(
                            "🚇🔄 <b>Повторная попытка собрать маршрут... Пожалуйста, подождите...</b>",
                        )
                        await asyncio.sleep(2)
                        await update_underground(message, user_id, state)
                        return
                else:
                    train_info = "🚇🚫 <b>К сожалению не удалось собрать путь до конечной станции. Попробуйте позже.</b>"
        else:
            last_valid_train_info = train_info

        if data.get('enable_auto_update'):
            if i < 119:
                remaining_time -= 30
                minutes, seconds = divmod(remaining_time, 60)
                duration_time = f'{int(minutes)} мин. {int(seconds)} сек.' if seconds else f'{int(minutes)} мин.'

                additional_text = f"\n🚇⌛ <b>Следующее обновление через каждые 30 секунд. Оставшееся время: {duration_time}</b>"
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🚫 | Отменить автообновление", callback_data="cancel_update")]
                ])
            else:
                additional_text = f"\n🚇⌛ <b>Автообновление завершено в {current_time}. Данные могут быть устаревшими.</b>"
                auto_update_users[user_id] = False
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🗑 | Удалить расписание", callback_data="delete_schedule")]
                ])

            train_info += additional_text
            media = InputMediaPhoto(media=random_image, caption=train_info)
            await message.edit_media(media, reply_markup=keyboard)
        else:
            additional_text = f"\n🚇 <b>Расписание вызвано в {current_time} без автообновления.</b>"
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🗑 | Удалить расписание", callback_data="delete_schedule")]
            ])
            train_info += additional_text
            media = InputMediaPhoto(media=random_image, caption=train_info)
            await message.edit_media(media, reply_markup=keyboard)
            auto_update_users[user_id] = False
            return
        await asyncio.sleep(30)


@dp.message(Command('underground'))
async def send_underground(message: Message, state: FSMContext):
    data = await state.get_data()
    from_station_underground = data.get('from_station_underground')
    to_station_underground = data.get('to_station_underground')
    user_id = message.chat.id
    tz = data.get('timezone', 'Europe/Moscow')

    if tz == 'Europe/Moscow':
        if auto_update_users.get(user_id, False):
            await message.reply("🚇↔ <b>Путь с автообновлением на данный момент активно. "
                                "Пожалуйста, отключите текущее автообновление перед запуском нового расписания.</b>")
            return

        if not from_station_underground or not to_station_underground:
            await message.reply("🚇 <b>Маршрут следования не был установлен. "
                                "Пожалуйста, установите маршрут перед построением пути следования до конечной станции.</b>")
            return
        else:
            initial_message = await message.reply("🚇↔ <b>Строим маршрут следования к конечной станции...</b>")
            try:
                await message.delete()
            except Exception:
                pass
            await update_underground(initial_message, user_id, state)
            await asyncio.sleep(10)

            try:
                await initial_message.edit_text("🚇🚫 <b>Не удалось получить информацию об маршруте следования. "
                                                "Попробуйте снова позже или проверьте правильность введенных станций. В случае многократного раза, обращайтесь в /feedback.</b>")
                auto_update_users[user_id] = False
            except Exception as e:
                pass
        await state.set_state()
    else:
        await message.reply("🚇️ℹ <b>Данная команда доступна жителям города «Москва». "
                            "Если вы являетесь жителем данного города и у вас нету доступа к этой команде, установите в настройках часовой пояс — Москва – UTC+3.</b>")
        return

    try:
        await message.delete()
    except Exception:
        pass


@dp.callback_query(lambda c: c.data == "send_underground")
async def handle_send_underground(callback_query: types.CallbackQuery, state: FSMContext):
    await send_underground(callback_query.message, state)
    await callback_query.message.delete()


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
        train_image_selector = ImageSelector(train_urls)
        random_image = train_image_selector.get_random_image()

        if not auto_update_users[user_id]:
            train_info += f"\n🛤🚫<b> Автообновление было отменено. Последние данные были обновлены в {current_time}.</b>"
            media = InputMediaPhoto(media=random_image, caption=train_info)
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
                media = InputMediaPhoto(media=random_image, caption=train_info)
                await message.edit_media(media, reply_markup=keyboard)
            else:
                additional_text = f"\n🛤 <b>Расписание было вызвано в {current_time} без автообновления, учтите актуальность данного расписания.</b>"
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🗑 | Удалить расписание", callback_data="delete_schedule")]
                ])

                train_info += additional_text
                media = InputMediaPhoto(media=random_image, caption=train_info)
                await message.edit_media(media, reply_markup=keyboard)
                auto_update_users[user_id] = False
                return
            await asyncio.sleep(60)
        else:
            await message.edit_text(
                "🚂🚫 <b>К сожалению, по вашему маршруту следования мы не нашли расписание. "
                "Пожалуйста, укажите действительный маршрут следования поезда дальнего следования.</b>")
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
                            )
        return

    if not from_city or not to_city:
        await message.reply("🚂🏙 <b>Маршрут следования не был установлен. "
                            "Пожалуйста, установите маршрут перед поиском расписания следования электричек.</b>",
                            )
        return
    else:
        initial_message = await message.reply("🚂🗓 <b>Получаем расписание поездов дальнего следования...</b>")
        try:
            await message.delete()
        except Exception:
            pass
        await update_trains(initial_message, user_id, state)
    await state.set_state()

    try:
        await message.delete()
    except Exception:
        pass


@dp.callback_query(lambda c: c.data == "send_train")
async def handle_send_train(callback_query: types.CallbackQuery, state: FSMContext):
    await send_trains(callback_query.message, state)
    await callback_query.message.delete()


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
                              InlineKeyboardButton(text="🚂 | Поезда дальнего следования", callback_data="send_train")],
                             [InlineKeyboardButton(text="🚇 | Московский метрополитен",
                                                   callback_data="send_underground")]])
    else:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🚉 | Пригородные поезда", callback_data="send_suburban"),
                              InlineKeyboardButton(text="🚂 | Поезда дальнего следования", callback_data="send_train")]])
    await callback_query.message.reply("🗓🔍 <b>Выберите какой тип транспорта вам необходимо узнать.</b>",
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


@dp.callback_query(lambda c: c.data == "support_developer")
async def handle_support_callback(callback_query: types.CallbackQuery):
    sent_message = await bot.send_message(
        chat_id=callback_query.message.chat.id,
        text=(
            '<b>⭐ℹ Если вы хотите, чтобы разработчику было приятно, вы можете поддержать его Telegram Stars! '
            'Заранее благодарим тех, кто решился нас поддержать! Для того, чтобы поддержать автора, пропишите команду: '
            '<i>/support "ЧИСЛО ОТ 1 ДО 5000"</i></b>'
        ),
    )
    await asyncio.sleep(15)
    await bot.delete_message(chat_id=sent_message.chat.id, message_id=sent_message.message_id)


@dp.message(Command('support'))
async def handle_support_message(message: types.Message):
    try:
        await message.delete()
    except Exception:
        pass

    parts = message.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        msg = await message.answer(
            '<b>⭐ℹ Пожалуйста, укажите сумму поддержки в звёздах: <i>/support "ЧИСЛО ОТ 1 ДО 5000"</i></b>')
        await asyncio.sleep(15)
        try:
            await msg.delete()
        except Exception:
            pass
        return

    amount = int(parts[1])
    if not (1 <= amount <= 5000):
        msg = await message.answer("<b>⭐❌ Сумма должна быть от 1 до 5000 звёзд.</b>")
        await asyncio.sleep(180)
        try:
            await msg.delete()
        except Exception:
            pass
        return

    prices = [LabeledPrice(label="XTR", amount=amount)]
    bot_msg = await bot.send_invoice(
        chat_id=message.chat.id,
        title="Поддержать разработчика",
        description="Подтверждая данную покупку, вы соглашаетесь с тем, что готовы пожертвовать разработчикам указанную вами сумму. "
                    "Оплатите поддержку в течении 3 минут, иначе сообщение с оплатой будет удалено.",
        currency="XTR",
        prices=prices,
        payload="support_developer",
    )
    await asyncio.sleep(180)
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=bot_msg.message_id)
    except Exception:
        pass


@dp.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@dp.message(F.successful_payment)
async def process_successful_payment(message: types.Message):
    await bot.send_message(chat_id=message.chat.id,
                           text='<b>⭐❤ Спасибо вам, что вы поддержали разработчика! Этим действием вы даете понять, что вы цените чужой труд!</b>',
                           message_effect_id="5159385139981059251")
    logging.info(f"Telegram Stars successful payment: {message.successful_payment.telegram_payment_charge_id}")


# Settings
@dp.callback_query(lambda c: c.data == "enable_auto_update")
async def handle_enable_auto_update(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    enable_auto_update = data.get('enable_auto_update', False)
    new_status = not enable_auto_update
    await state.update_data(enable_auto_update=new_status)

    express_type = data.get('express_type', False)
    express_text = "🚅 | Только экспрессы" if express_type else "🚆 | Обычные и экспрессы"

    emoji = "✅" if new_status else "❌"
    settings_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{emoji} | Автообновление", callback_data="enable_auto_update"),
             InlineKeyboardButton(text="🚮 | Очистка маршрутов", callback_data="clear_route")],
            [InlineKeyboardButton(text="🔁 | Инверсия маршрута", callback_data="inversion_route")],
            [InlineKeyboardButton(text="🕒 | Часовой пояс", callback_data="select_timezone")],
            [InlineKeyboardButton(text=express_text, callback_data="toggle_express_type")],
            [InlineKeyboardButton(text="⬅ | Назад", callback_data="back")]
        ])
    await bot.edit_message_reply_markup(chat_id=callback_query.message.chat.id,
                                        message_id=callback_query.message.message_id,
                                        reply_markup=settings_keyboard)


@dp.callback_query(lambda c: c.data == "settings")
async def handle_settings(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    enable_auto_update = data.get('enable_auto_update', False)
    express_type = data.get('express_type', False)
    emoji = "✅" if enable_auto_update else "❌"
    express_text = "🚅 | Только экспрессы" if express_type else "🚆 | Обычные и экспрессы"
    settings_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{emoji} | Автообновление", callback_data="enable_auto_update"),
             InlineKeyboardButton(text="🚮 | Очистка маршрутов", callback_data="clear_route")],
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

    enable_auto_update = data.get('enable_auto_update', False)
    emoji = "✅" if enable_auto_update else "❌"
    express_text = "🚅 | Только экспрессы" if new_express_type else "🚆 | Обычные и экспрессы"

    settings_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{emoji} | Автообновление", callback_data="enable_auto_update"),
             InlineKeyboardButton(text="🚮 | Очистка маршрутов", callback_data="clear_route")],
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
        message_prefix = "поездов дальнего следования"
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


# Debug
@dp.message(Command('feedback'))
@dp.callback_query(lambda c: c.data == 'feedback')
async def feedback_command(event, state: FSMContext):
    user_state = await state.get_data()

    if user_state.get('feedback_in_progress'):
        if isinstance(event, Message):
            await event.answer(
                "ℹ✉ <b>У вас уже есть одно открытое обращение. Пожалуйста, дождитесь ответа. Если вам уже ответили на обращение, то отметьте его прочитанным, перед тем, как написать следующее.</b>",
            )
        elif isinstance(event, CallbackQuery):
            await event.message.answer(
                "ℹ✉ <b>У вас уже есть одно открытое обращение. Пожалуйста, дождитесь ответа. Если вам уже ответили на обращение, то отметьте его прочитанным, перед тем, как написать следующее.</b>",
            )
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ | Отменить обращение", callback_data="cancel_feedback")]
        ])

    if isinstance(event, Message):
        feedback_message = await event.answer(
            "📨 <b>Пожалуйста, напишите ваше сообщение, которое будет передано создателю бота. \n\n</b>"
            "В своем сообщении вы можете рассказать об пожеланиях, обнаруженных ошибках и багах, оставить отзыв по поводу использования бота. "
            "Убедительная просьба, не писать в обратную связь всякий не связанный бред, имейте уважение.",
            reply_markup=keyboard)
    elif isinstance(event, CallbackQuery):
        feedback_message = await event.message.answer(
            "📨 <b>Пожалуйста, напишите ваше сообщение, которое будет передано создателю бота. \n\n</b>"
            "В своем сообщении вы можете рассказать об пожеланиях, обнаруженных ошибках и багах, оставить отзыв по поводу использования бота. "
            "Убедительная просьба, не писать в обратную связь всякий не связанный бред, имейте уважение.",
            reply_markup=keyboard)

    await state.update_data(feedback_message_id=feedback_message.message_id, feedback_chat_id=feedback_message.chat.id)
    await state.set_state(FeedbackStates.awaiting_feedback)

    try:
        await event.delete()
    except Exception:
        pass


@dp.message(FeedbackStates.awaiting_feedback)
async def handle_feedback(message: Message, state: FSMContext):
    feedback_text = message.text
    user = message.from_user
    state_data = await state.get_data()
    feedback_message_id = state_data.get('feedback_message_id')
    feedback_chat_id = state_data.get('feedback_chat_id')

    feedback_message = (
        f"💌 <b>У вас появилось новое обращение от {user.full_name} (@{user.username}):</b>\n\n{feedback_text}\n\n"
        f"<b>Для ответа пользователю используйте кнопку ниже.</b>"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✉️ | Ответить пользователю", callback_data=f"reply_{user.id}")]
        ]
    )

    await bot.send_message(chat_id=admin_id, text=feedback_message, reply_markup=keyboard)
    await bot.edit_message_text("📧 <b>Спасибо за обратную связь! В течении времени вам ответит создатель бота.</b>",
                                chat_id=feedback_chat_id,
                                message_id=feedback_message_id,
                                )
    await state.update_data(feedback_in_progress=True)
    await state.set_state()


@dp.callback_query(lambda c: c.data.startswith("reply_"))
async def ask_reply_text(callback_query: CallbackQuery, state: FSMContext):
    if callback_query.message.chat.id != int(admin_id):
        return
    user_id = int(callback_query.data.split("_")[1])
    reply_prompt_message = await bot.send_message(chat_id=admin_id,
                                                  text="📝 <b>Пожалуйста, введите текст ответа пользователю:</b>")
    await state.update_data(reply_user_id=user_id, reply_prompt_message_id=reply_prompt_message.message_id)
    await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
    await state.set_state(FeedbackStates.awaiting_reply_text)


@dp.callback_query(lambda c: c.data == 'cancel_feedback')
async def cancel_feedback_reply_text(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_text("❌📧 <b>Вы отменили обратную связь с создателем бота.</b>")
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
    reply_prompt_message_id = state_data.get('reply_prompt_message_id')

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ | Пометить прочитанным", callback_data="read_feedback")]
        ]
    )

    try:
        await bot.send_message(chat_id=user_id,
                               text=f"📩 <b>Вам поступило сообщение от создателя бота в ответ на ваше обращение:</b>\n\n{reply_text}",
                               reply_markup=keyboard)
        await bot.edit_message_text("📧 <b>Сообщение было успешно отправлено пользователю.</b>",
                                    chat_id=admin_id,
                                    message_id=reply_prompt_message_id)
    except Exception as e:
        await message.answer(f"❌ <b>Не удалось отправить сообщение пользователю. Ошибка:</b> {e}")
    await state.set_state()


@dp.message(Command('log'))
async def send_log_file(message: Message, state: FSMContext):
    data = await state.get_data()
    debug_menu = data.get('debug_menu')
    if debug_menu:
        log_file_path = 'YandexRaspBot-error.log'
        if os.path.exists(log_file_path):
            await message.answer_document(FSInputFile(log_file_path),
                                          caption="✅⚙ <b>Файл логов был найден, отправляю его вам! Чтобы снова вызвать и получить логи, также воспользуйтесь командой /log.</b>")
        else:
            await message.answer(
                "❌⚙ <b>Файл логов не был найден. Скорее всего его не существует в текущей директории сервера.</b>")
    else:
        await state.update_data(debug_menu=False)


@dp.message(Command('refund'))
async def command_refund_handler(message: types.Message, state: FSMContext):
    parts = message.text.strip().split()
    data = await state.get_data()
    debug_menu = data.get('debug_menu')
    if debug_menu:
        if len(parts) < 2:
            await message.answer("<b>ℹ Пожалуйста, укажите ID транзакции.</b>")
            return

        transaction_id = parts[1]
        try:
            await bot.refund_star_payment(
                user_id=message.from_user.id,
                telegram_payment_charge_id=transaction_id)
            logging.info(f"Telegram Stars refund request completed: {transaction_id}")
        except Exception as e:
            logging.info(f"Error when returning Telegram Stars: {e}")
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
                             "<b>Для просмотра информации из данных API, требуется зайти на https://www.postman.com/ и вставить туда ссылку либо открыть ссылку в браузере.</b>")
    else:
        await state.update_data(debug_menu=False)


if __name__ == '__main__':
    bot = Bot(token=token_bot, default=DefaultBotProperties(parse_mode='HTML'))
    asyncio.run(dp.start_polling(bot))

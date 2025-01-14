import asyncio
import locale
import logging
import os
import random
from datetime import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.mongo import MongoStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, Message
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
admin_id = int(os.getenv('ADMIN_ID'))

config = load_config()
image_urls = config.image_urls
dp = Dispatcher(storage=MongoStorage(client=AsyncIOMotorClient()).from_url(
    os.getenv("MONGO_URL")))
dp.include_router(route_selector)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%d-%m-%y %H:%M:%S')
auto_update_users = {}

async def update_suburbans(message: Message, user_id: int, state: FSMContext):
    remaining_time = 60
    data = await state.get_data()
    from_station = data.get('from_station')
    to_station = data.get('to_station')
    auto_update_users[user_id] = True

    for i in range(60):
        current_time = datetime.now().strftime('%H:%M')
        train_info = get_suburban_info(from_station, to_station)
        random_image = random.choice(image_urls)

        if not auto_update_users[user_id]:
            train_info += f"\n🚆🚫<b> Автообновление было отменено. Последние данные были обновлены в {current_time}.</b>"
            media = InputMediaPhoto(media=random_image, caption=train_info, parse_mode='HTML')
            await message.edit_media(media)
            auto_update_users[user_id] = False
            return

        if train_info:
            if data.get('enable_auto_update'):
                if i < 59:
                    remaining_time -= 1
                    additional_text = f"\n<b>🚆⌛ Следующее обновление через 1 минуту. Оставшееся время обновления: {remaining_time} минут.</b>"
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(
                        text="🚫 | Отменить автообновление", callback_data="cancel_update")]])
                else:
                    additional_text = f"\n<b>🚆⌛ Автообновление было завершено в {current_time}, учтите актуальность данного расписания!</b>"
                    auto_update_users[user_id] = False
                    keyboard = None

                train_info += additional_text
                media = InputMediaPhoto(media=random_image, caption=train_info, parse_mode='HTML')
                await message.edit_media(media, reply_markup=keyboard)
            else:
                additional_text = f"\n<b>🚉 Расписание было вызвано в {current_time} без автообновления, учтите актуальность данного расписания!</b>"

                train_info += additional_text
                media = InputMediaPhoto(media=random_image, caption=train_info, parse_mode='HTML')
                await message.edit_media(media)
                auto_update_users[user_id] = False
                return
            await asyncio.sleep(60)
        else:
            await message.edit_text(
                "🚆🚫 <b>К сожалению, по вашему маршруту следования мы не нашли расписание. "
                "Пожалуйста, укажите действительный маршрут следования электрички.</b>",
                parse_mode='HTML')
            auto_update_users[user_id] = False
            return

async def update_trains(message: Message, user_id: int, state: FSMContext):
    remaining_time = 60
    data = await state.get_data()
    from_city = data.get('from_city')
    to_city = data.get('to_city')
    auto_update_users[user_id] = True

    for i in range(60):
        current_time = datetime.now().strftime('%H:%M')
        train_info = get_train_info(from_city, to_city)
        random_image = random.choice(image_urls)

        if not auto_update_users[user_id]:
            train_info += f"\n🚆🚫<b> Автообновление было отменено. Последние данные были обновлены в {current_time}.</b>"
            media = InputMediaPhoto(media=random_image, caption=train_info, parse_mode='HTML')
            await message.edit_media(media)
            auto_update_users[user_id] = False
            return

        if train_info:
            if data.get('enable_auto_update'):
                if i < 59:
                    remaining_time -= 1
                    additional_text = f"\n<b>🚆⌛ Следующее обновление через 1 минуту. Оставшееся время обновления: {remaining_time} минут.</b>"
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(
                        text="🚫 | Отменить автообновление", callback_data="cancel_update")]])
                else:
                    additional_text = f"\n<b>🚆⌛ Автообновление было завершено в {current_time}, учтите актуальность данного расписания!</b>"
                    auto_update_users[user_id] = False
                    keyboard = None

                train_info += additional_text
                media = InputMediaPhoto(media=random_image, caption=train_info, parse_mode='HTML')
                await message.edit_media(media, reply_markup=keyboard)
            else:
                additional_text = f"\n<b>🚂 Расписание было вызвано в {current_time} без автообновления, учтите актуальность данного расписания!</b>"

                train_info += additional_text
                media = InputMediaPhoto(media=random_image, caption=train_info, parse_mode='HTML')
                await message.edit_media(media)
                auto_update_users[user_id] = False
                return
            await asyncio.sleep(60)
        else:
            await message.edit_text(
                "🚆🚫 <b>К сожалению, по вашему маршруту следования мы не нашли расписание. "
                "Пожалуйста, укажите действительный маршрут следования электрички.</b>",
                parse_mode='HTML')
            auto_update_users[user_id] = False
            return

@dp.message(CommandStart())
async def send_welcome(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅ | Указать маршрут", callback_data="find_route"), InlineKeyboardButton(text="⚙ | Настройки", callback_data="settings")],
                         [InlineKeyboardButton(text="📋 | Расписание ", callback_data="schedule")]])

    random_image = random.choice(image_urls)
    await message.answer_photo(photo=random_image,
                               caption="📋 <b>Расписание пригородных электричек и экспрессов</b>\n\n"
                                       "Данный бот позволяет вам быстро узнать расписание об вашей электричке или поездах. Для этого нужно лишь указать ОТКУДА и КУДА вам надо поехать и появиться полная информация об ближайших пригородных электричек и поездах.\n\n"
                                       "Для того, чтобы изменить маршрут следования или узнать расписание по текущему маршруту, нажмите кнопки ниже, либо воспользуйтесь командами /suburban и /route.",
                               parse_mode='HTML', reply_markup=keyboard)

@dp.message(Command('suburban'))
async def send_suburbans(message: Message, state: FSMContext):
    data = await state.get_data()
    from_station = data.get('from_station')
    to_station = data.get('to_station')
    user_id = message.chat.id

    if auto_update_users.get(user_id, False):
        await message.reply("🚆📋 <b>Расписание с автообновление на данный момент активно. "
                            "Пожалуйста, отключите текущее автообновление перед запуском нового расписания.</b>",
                            parse_mode='HTML')
        return

    if not from_station or not to_station:
        await message.reply("🚆🛃 <b>Маршрут следования не был установлен. "
                            "Пожалуйста, установите маршрут перед поиском расписания следования электричек.</b>",
                            parse_mode='HTML')
        return
    else:
        initial_message = await message.reply("🚆📋 <b>Получаем расписание электричек...</b>", parse_mode='HTML')
        await update_suburbans(initial_message, user_id, state)

@dp.message(Command('train'))
async def send_trains(message: Message, state: FSMContext):
    data = await state.get_data()
    from_city = data.get('from_city')
    to_city = data.get('to_city')
    user_id = message.chat.id

    if auto_update_users.get(user_id, False):
        await message.reply("🚂📋 <b>Расписание с автообновление на данный момент активно. "
                            "Пожалуйста, отключите текущее автообновление перед запуском нового расписания.</b>",
                            parse_mode='HTML')
        return

    if not from_city or not to_city:
        await message.reply("🚂🛃 <b>Маршрут следования не был установлен. "
                            "Пожалуйста, установите маршрут перед поиском расписания следования электричек.</b>",
                            parse_mode='HTML')
        return
    else:
        initial_message = await message.reply("🚂📋 <b>Получаем расписание поездов...</b>", parse_mode='HTML')
        await update_trains(initial_message, user_id, state)

@dp.callback_query(lambda c: c.data == 'cancel_update')
async def cancel_update(callback_query: types.CallbackQuery):
    user_id = callback_query.message.chat.id
    auto_update_users[user_id] = False
    await bot.answer_callback_query(callback_query.id,
                                    text="🚫⌛ Автообновление было отменено, учтите что данные могут быть неактуальными. Отмена произойдет в течении минуты.")
    await bot.edit_message_reply_markup(callback_query.message.business_connection_id, callback_query.message.chat.id,
                                        callback_query.message.message_id,
                                        reply_markup=None)

@dp.callback_query(lambda c: c.data == "send_suburban")
async def handle_send_suburban(callback_query: types.CallbackQuery, state: FSMContext):
    await send_suburbans(callback_query.message, state)

@dp.callback_query(lambda c: c.data == "send_train")
async def handle_send_suburban(callback_query: types.CallbackQuery, state: FSMContext):
    await send_trains(callback_query.message, state)

@dp.callback_query(lambda c: c.data == "schedule")
async def handle_schedule(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🚉 | Электрички", callback_data="send_suburban"), InlineKeyboardButton(text="🚂 | Поезда", callback_data="send_train")]])
    await callback_query.message.reply("📋🔍 <b>Выберите то расписание транспорта, которое вам необходимо узнать.</b>", parse_mode='HTML', reply_markup=keyboard)

@dp.callback_query(lambda c: c.data == "enable_auto_update")
async def handle_enable_auto_update(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    enable_auto_update = data.get('enable_auto_update', False)
    new_status = not enable_auto_update
    await state.update_data(enable_auto_update=new_status)

    emoji = "✅" if new_status else "❌"
    settings_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=f"{emoji} | Автообновление", callback_data="enable_auto_update"),
                         InlineKeyboardButton(text="🚮 | Очистка маршрута", callback_data="clear_route")],
                         [InlineKeyboardButton(text="⬅ | Назад", callback_data="back")]])
    await bot.edit_message_reply_markup(chat_id=callback_query.message.chat.id,
                                        message_id=callback_query.message.message_id,
                                        reply_markup=settings_keyboard)

@dp.callback_query(lambda c: c.data == "settings")
async def handle_settings(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    enable_auto_update = data.get('enable_auto_update', False)
    emoji = "✅" if enable_auto_update else "❌"
    settings_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=f"{emoji} | Автообновление", callback_data="enable_auto_update"),
                         InlineKeyboardButton(text="🚮 | Очистка маршрута", callback_data="clear_route")],
                         [InlineKeyboardButton(text="⬅ | Назад", callback_data="back")]])
    await bot.edit_message_reply_markup(chat_id=callback_query.message.chat.id,
                                        message_id=callback_query.message.message_id,
                                        reply_markup=settings_keyboard)

@dp.callback_query(lambda c: c.data == "clear_route")
async def clear_route(callback_query: types.CallbackQuery, state: FSMContext):
    await state.update_data(from_station=None, to_station=None)
    await bot.send_message(callback_query.message.chat.id, "🚆🚮 <b>Маршрут следования был успешно очищен. Для того, чтобы установить новый маршрут, воспользуйтесь командой /route.</b>", parse_mode='HTML')

@dp.callback_query(lambda c: c.data == "back")
async def handle_back(callback_query: types.CallbackQuery):
    main_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅ | Указать маршрут", callback_data="find_route_city"), InlineKeyboardButton(text="⚙ | Настройки", callback_data="settings")],
                         [InlineKeyboardButton(text="📋 | Расписание", callback_data="schedule")]])
    await bot.edit_message_reply_markup(chat_id=callback_query.message.chat.id,
                                        message_id=callback_query.message.message_id,
                                        reply_markup=main_keyboard)

@dp.message(Command('log'))
async def send_log_file(message: Message):
    if message.from_user.id == admin_id:
        log_file_path = 'YandexRaspBot-error.log'
        if os.path.exists(log_file_path):
            await message.answer_document(FSInputFile(log_file_path), caption="✅⚙ <b>Файл логов был найден, отправляю его вам!</b>", parse_mode='HTML')
        else:
            await message.answer("❌⚙ <b>Файл логов не найден.</b>", parse_mode='HTML')

if __name__ == '__main__':
    bot = Bot(token=token_bot)
    asyncio.run(dp.start_polling(bot))
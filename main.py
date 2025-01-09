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
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, Message
from dotenv import load_dotenv

from src.get_train_info import get_train_info
from src.utils.load_config import load_config
from src.route_select.route_selector import route_selector

load_dotenv()
locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

token_yandex = os.getenv('TOKEN_YANDEX')
token_bot = os.getenv('TOKEN_BOT')

config = load_config()
image_urls = config.image_urls
dp = Dispatcher()
dp.include_router(route_selector)

logging.basicConfig(level=logging.INFO)


async def update_trains(message: Message, state: FSMContext):
    remaining_time = 60
    data = await state.get_data()
    from_station = data.get('from_station')
    to_station = data.get('to_station')
    await state.update_data(autoupdate=True)

    for i in range(60):
        current_time = datetime.now().strftime('%H:%M')
        train_info = get_train_info(from_station, to_station)
        random_image = random.choice(image_urls)
        data = await state.get_data()

        if not data.get("autoupdate"):
            train_info += f"\n🚆🚫<b> Автообновление было отменено. Последние данные были обновлены в {current_time}.</b>"
            media = InputMediaPhoto(media=random_image, caption=train_info, parse_mode='HTML')
            await message.edit_media(media)
            await state.update_data(autoupdate=False)
            return

        if train_info:
            if i < 59:
                remaining_time -= 1
                additional_text = f"\n<b>🚆⌛ Следующее обновление через 1 минуту. Оставшееся время обновления: {remaining_time} минут.</b>"
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(
                    text="🚫 | Отменить автообновление", callback_data=f"cancel_update")]])

            else:
                additional_text = f"\n<b>🚆⌛ Автообновление было завершено в {current_time}, учтите актуальность данного расписания!</b>"
                await state.update_data(autoupdate=False)
                keyboard = None

            train_info += additional_text
            media = InputMediaPhoto(media=random_image, caption=train_info, parse_mode='HTML')
            await message.edit_media(media, reply_markup=keyboard)
        else:
            await message.edit_text(
                "🚆🚫 <b>К сожалению, по вашему маршруту следования мы не нашли расписание. "
                "Пожалуйста, укажите действительный маршрут следования электрички.</b>",
                parse_mode='HTML')
            await state.update_data(autoupdate=False)
            return
        await asyncio.sleep(60)


@dp.message(CommandStart())
async def send_welcome(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅ | Указать маршрут", callback_data="find_route")],
                         [InlineKeyboardButton(text="🚆 | Расписание электричек", callback_data="send_suburban")]])

    random_image = random.choice(image_urls)
    await message.answer_photo(photo=random_image,
                               caption="📋 <b>Расписание пригородных электричек и экспрессов</b>\n\n"
                                       "Данный бот позволяет вам быстро узнать расписание об вашем поезде. Для этого нужно лишь указать откуда и куда вам надо приехать и появиться полная информация об ближайших пригородных электричек и поездах.\n\n"
                                       "Для того, чтобы изменить или узнать расписание по текущим указаниям маршрута, нажмите кнопки ниже.",
                               parse_mode='HTML', reply_markup=keyboard)

@dp.message(Command('suburban'))
async def send_trains(message: Message, state: FSMContext):
    data = await state.get_data()
    from_station = data.get('from_station')
    to_station = data.get('to_station')

    if (await state.get_data()).get("autoupdate"):
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
        initial_message = await message.reply("🚆📋 <b>Получаем расписание поездов...</b>", parse_mode='HTML')
        await update_trains(initial_message, state)


@dp.callback_query(lambda c: c.data == 'cancel_update')
async def cancel_update(callback_query: types.CallbackQuery, state: FSMContext):
    await state.update_data(autoupdate=False)
    await bot.answer_callback_query(callback_query.id,
                                    text="🚫⌛ Автообновление было отменено, учтите что данные могут быть неактуальными. Отмена произойдет в течении минуты.")
    await bot.edit_message_reply_markup(callback_query.message.business_connection_id, callback_query.message.chat.id,
                                        callback_query.message.message_id,
                                        reply_markup=None)


@dp.callback_query(lambda c: c.data == "send_suburban")
async def handle_send_suburban(callback_query: types.CallbackQuery, state: FSMContext):
    await send_trains(callback_query.message, state)


if __name__ == '__main__':
    bot = Bot(token=token_bot)
    asyncio.run(dp.start_polling(bot))

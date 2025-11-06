from datetime import datetime, timedelta

from aiogram import types, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from aiogram.filters import Command

from src.requests.get_scooters_info import get_scooters_info
from src.utils.Image_selector import ImageSelector
from src.utils.load_config import load_config

scooters = Router()

config = load_config()
scooters_urls = config.scooters_urls

user_message_ids = {}
last_update_time = {
    "scooters": {}
}


class ScootersStates(StatesGroup):
    awaiting_location = State()


@scooters.message(Command("scooters"))
async def request_location(message: Message, state: FSMContext):
    await message.delete()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚫 | Отменить поиск", callback_data="delete_message")]
    ])
    sent = await message.answer(
        "🛴📍<b>Для поиска ближайших электросамокатов необходимо отправить свое местоположения. "
        "Пожалуйста отправьте точку вашего местоположения</b>", reply_markup=keyboard)
    user_message_ids[message.from_user.id] = sent.message_id
    await state.set_state(ScootersStates.awaiting_location)


@scooters.message(ScootersStates.awaiting_location)
async def handle_location(message: Message, state: FSMContext):
    user_id = message.chat.id
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚫 | Отменить поиск", callback_data="delete_message")]
    ])

    if not message.location:
        await message.delete()
        message_scooters = user_message_ids.get(message.from_user.id)
        if message_scooters:
            try:
                await message.bot.edit_message_text(
                    chat_id=user_id,
                    message_id=message_scooters,
                    text="🛴⚠ <b>Пожалуйста, отправьте свое местоположения для получения данных об ближайших электросамокатах.</b>",
                    reply_markup=keyboard)
            except Exception:
                pass
        return

    lat = message.location.latitude
    lon = message.location.longitude
    current_time = datetime.now().strftime('%H:%M')

    scooters_image_selector = ImageSelector(scooters_urls)
    random_image = scooters_image_selector.get_random_image()

    await message.delete()
    message_scooters = user_message_ids.get(message.from_user.id)
    await message.bot.edit_message_text(chat_id=user_id, message_id=message_scooters,
                                        text="🛴⌛ <b>Получаем данные об ближайших электросамокатах от вашего местоположения... "
                                             "Это может занять некоторое время...</b>")

    scooters_info = get_scooters_info(lat, lon)
    if scooters_info:
        additional_text = f"\n🛴 <b>Последнее обновление в {current_time}. Вы можете обновить данные об ближайших электросамокатах вручную раз в минуту.</b>"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 | Обновить информацию", callback_data=f"updatescooters_{lat}_{lon}")],
            [InlineKeyboardButton(text="🗑 | Удалить информацию", callback_data="delete_message")]
        ])
        scooters_info += additional_text
        last_update_time["scooters"][user_id] = datetime.now()
        media = InputMediaPhoto(media=random_image, caption=scooters_info)
        await message.bot.edit_message_media(chat_id=message.chat.id, message_id=message_scooters,
                                             reply_markup=keyboard, media=media)
        await state.set_state(None)
    else:
        await message.bot.edit_message_text(chat_id=message.chat.id, message_id=message_scooters,
                                            text="🛴🚫 <b>В указанной вами точки вашего местоположения не найдены электросамокаты. "
                                                 "Пожалуйста, попробуйте указать другую точку вашего местоположения.</b>",reply_markup=keyboard)


@scooters.callback_query(lambda c: c.data.startswith("updatescooters_"))
async def handle_manual_update_scooters(callback_query: types.CallbackQuery):
    _, lat_locate, lon_locate = callback_query.data.split("_")
    user_id = callback_query.from_user.id
    now = datetime.now()

    last_time = last_update_time["scooters"].get(user_id)
    if last_time and now - last_time < timedelta(minutes=1):
        await callback_query.answer("🔄 Подождите немного перед следующим обновлением.", show_alert=True)
        return

    last_update_time["scooters"][user_id] = now
    await update_scooters(callback_query.message, float(lat_locate), float(lon_locate))
    await callback_query.answer("🛴🔄 Данные об электросамокатах обновлены.")


async def update_scooters(message: Message, lat: float, lon: float):
    user_id = message.chat.id
    current_time = datetime.now().strftime('%H:%M')

    scooters_image_selector = ImageSelector(scooters_urls)
    random_image = scooters_image_selector.get_random_image()

    scooters_info = get_scooters_info(lat, lon)
    if scooters_info:
        additional_text = f"\n🛴 <b>Последнее обновление в {current_time}. Вы можете обновить данные об ближайших электросамокатах вручную раз в минуту.</b>"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 | Обновить информацию", callback_data=f"updatescooters_{lat}_{lon}")],
            [InlineKeyboardButton(text="🗑 | Удалить информацию", callback_data="delete_message")]
        ])
        scooters_info += additional_text
        last_update_time["scooters"][user_id] = datetime.now()
        media = InputMediaPhoto(media=random_image, caption=scooters_info)
        await message.bot.edit_message_media(chat_id=message.chat.id, message_id=message.message_id,
                                             reply_markup=keyboard, media=media)
    else:
        await message.bot.edit_message_text(chat_id=message.chat.id, message_id=message,
                                            text="🛴⚠ <b>В указанной вами точки вашего местоположения не найдены электросамокаты. "
                                                 "Возможно, все доступные электросамокаты в радиусе 200 м. были разобраны.</b>")

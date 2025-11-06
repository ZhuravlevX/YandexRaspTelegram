from pytz import timezone
from datetime import datetime, timedelta

from aiogram import types, Router
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, Message, CallbackQuery
from src.requests.get_intercity_bus_info import get_intercity_bus_info
from src.requests.get_plane_info import get_plane_info
from src.requests.get_suburban_info import get_suburban_info
from src.requests.get_train_info import get_train_info
from src.requests.get_tramway_info import get_tramway_info
from src.requests.get_underground_info import get_underground_info
from src.utils.Image_selector import ImageSelector
from src.utils.load_config import load_config

schedule = Router()

config = load_config()
train_urls = config.train_urls
tramway_urls = config.tramway_urls
plane_urls = config.plane_urls
underground_urls = config.underground_urls
suburban_urls = config.suburban_urls
russian_timezones = config.russian_timezones

last_update_time = {
    "tramway": {},
    "suburban": {},
    "underground": {},
    "train": {},
    "intercity_bus": {},
    "plane": {}
}

# Suburbans
@schedule.message(Command('suburban'))
async def send_suburbans(message: Message, state: FSMContext):
    data = await state.get_data()
    from_station = data.get('from_station')
    to_station = data.get('to_station')
    express_type = data.get('express_type', False)

    user_id = message.chat.id

    if not from_station or not to_station:
        await message.reply("🚆🏫 <b>Маршрут следования не был установлен. "
                            "Пожалуйста, установите маршрут перед поиском расписания следования пригородных поездов.</b>")
        try:
            await message.delete()
        except Exception:
            pass
        return

    initial_message = await message.reply("🚆🗓 <b>Получаем расписание пригородных поездов...</b>")
    try:
        await message.delete()
    except Exception:
        pass

    last_update_time["suburban"][user_id] = datetime.now()
    await update_suburbans(initial_message, user_id, state, from_station, to_station, express_type)
    await state.set_state()


@schedule.callback_query(lambda c: c.data.startswith("updatesuburban_"))
async def handle_manual_update(callback_query: CallbackQuery, state: FSMContext):
    _, from_station, to_station, express_type_str = callback_query.data.split("_")
    express_type = express_type_str.lower() == 'true'

    user_id = callback_query.from_user.id
    now = datetime.now()

    last_time = last_update_time["suburban"].get(user_id)
    if last_time and now - last_time < timedelta(minutes=1):
        await callback_query.answer("🔄 Подождите немного перед следующим обновлением.", show_alert=True)
        return

    last_update_time["suburban"][user_id] = now
    await update_suburbans(callback_query.message, user_id, state, from_station, to_station, express_type)
    await callback_query.answer()


async def update_suburbans(message: Message, user_id: int, state: FSMContext, from_station: str, to_station: str,
                           express_type: bool):
    data = await state.get_data()
    tz = timezone(data.get('timezone', 'Europe/Moscow'))

    current_time = datetime.now(tz).strftime('%H:%M')
    train_info = get_suburban_info(from_station, to_station, str(tz), express_type)
    suburban_image_selector = ImageSelector(suburban_urls)
    random_image = suburban_image_selector.get_random_image()

    if train_info:
        print(f"updatesuburban_{to_station}_{from_station}_{str(express_type)}")
        additional_text = f"\n🏫 <b>Последнее обновление в {current_time}. Вы можете обновить или сделать инверсию расписание вручную раз в минуту.</b>"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 | Обновить",
                                  callback_data=f"updatesuburban_{from_station}_{to_station}_{str(express_type)}"),
             InlineKeyboardButton(text="🔁 | Инверсия",
                                  callback_data=f"updatesuburban_{to_station}_{from_station}_{str(express_type)}")],
            [InlineKeyboardButton(text="🗑 | Удалить расписание", callback_data="delete_message")]
        ])
        train_info += additional_text
        media = InputMediaPhoto(media=random_image, caption=train_info)
        await message.edit_media(media, reply_markup=keyboard)
    else:
        await message.edit_text(
            "🚆🚫 <b>К сожалению, по вашему маршруту следования мы не нашли расписание. "
            "Пожалуйста, укажите действительный маршрут следования пригородного поезда.</b>"
        )


@schedule.callback_query(lambda c: c.data == "send_suburban")
async def handle_send_suburban(callback_query: CallbackQuery, state: FSMContext):
    await send_suburbans(callback_query.message, state)
    await callback_query.message.delete()


# Tramway
@schedule.message(Command('tramway'))
async def send_tramway(message: Message, state: FSMContext):
    data = await state.get_data()
    stop_id = data.get('stop_id')
    user_id = message.chat.id
    tz = data.get('timezone', 'Europe/Moscow')

    if tz != 'Europe/Moscow':
        await message.reply("🚊ℹ <b>Данная команда доступна жителям города «Москва». "
                            "Если вы являетесь жителем данного города и у вас нет доступа к этой команде, установите в настройках часовой пояс — Москва – UTC+3.</b>")
        return

    initial_message = await message.reply("🚊🗓 <b>Получаем расписание трамваев на остановке...</b>")
    try:
        await message.delete()
    except Exception:
        pass

    last_update_time["tramway"][user_id] = datetime.now()
    await update_tramway(initial_message, user_id, state)
    await state.set_state()


@schedule.callback_query(lambda c: c.data == "manual_update_tramway")
async def handle_manual_update_tramway(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    now = datetime.now()

    last_time = last_update_time["tramway"].get(user_id)
    if last_time and now - last_time < timedelta(minutes=1):
        await callback_query.answer("🔄 Подождите немного перед следующим обновлением.", show_alert=True)
        return

    last_update_time["tramway"][user_id] = now
    await update_tramway(callback_query.message, user_id, state)
    await callback_query.answer("🚊🔄 Расписание обновлено.")


async def update_tramway(message: Message, user_id: int, state: FSMContext):
    data = await state.get_data()
    stop_id = data.get('stop_id')
    tz = timezone(data.get('timezone', 'Europe/Moscow'))
    current_time = datetime.now(tz).strftime('%H:%M')

    tramway_info = get_tramway_info(stop_id)
    tramway_image_selector = ImageSelector(tramway_urls)
    random_image = tramway_image_selector.get_random_image()

    if tramway_info:
        additional_text = f"\n🚊 <b>Последнее обновление в {current_time}. Вы можете обновить расписание вручную раз в минуту.</b>"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 | Обновить расписание", callback_data="manual_update_tramway")],
            [InlineKeyboardButton(text="🗑 | Удалить расписание", callback_data="delete_message")]
        ])
        tramway_info += additional_text
        media = InputMediaPhoto(media=random_image, caption=tramway_info)
        await message.edit_media(media, reply_markup=keyboard)
    else:
        await message.edit_text(
            "🚊🚫 <b>К сожалению, не удалось получить информацию о трамваях. "
            "Пожалуйста, проверьте правильность остановки и попробуйте позже.</b>"
        )


@schedule.callback_query(lambda c: c.data == "send_tramway")
async def handle_send_tramway(callback_query: CallbackQuery, state: FSMContext):
    await send_tramway(callback_query.message, state)
    await callback_query.message.delete()


# Undergrounds
async def update_underground(message: Message, user_id: int, state: FSMContext):
    data = await state.get_data()
    tz = timezone(data.get('timezone', 'Europe/Moscow'))

    from_station_underground = data.get('from_station_underground')
    to_station_underground = data.get('to_station_underground')
    current_time = datetime.now(tz).strftime('%H:%M')

    train_info = get_underground_info(from_station_underground, to_station_underground)
    underground_image_selector = ImageSelector(underground_urls)
    random_image = underground_image_selector.get_random_image()

    if train_info:
        additional_text = f"\n🚇 <b>Последнее обновление в {current_time}. Вы можете обновить маршрут вручную раз в минуту.</b>"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 | Обновить расписание", callback_data="manual_update_underground")],
            [InlineKeyboardButton(text="🗑 | Удалить маршрут", callback_data="delete_message")]
        ])
        train_info += additional_text
        media = InputMediaPhoto(media=random_image, caption=train_info)
        await message.edit_media(media, reply_markup=keyboard)
    else:
        await message.edit_text(
            "🚇🚫 <b>К сожалению, не удалось построить маршрут. "
            "Проверьте правильность станций и попробуйте позже.</b>"
        )


@schedule.message(Command('underground'))
async def send_underground(message: Message, state: FSMContext):
    data = await state.get_data()
    from_station_underground = data.get('from_station_underground')
    to_station_underground = data.get('to_station_underground')
    user_id = message.chat.id
    tz = data.get('timezone', 'Europe/Moscow')

    if tz != 'Europe/Moscow':
        await message.reply("🚇️ℹ <b>Данная команда доступна жителям города «Москва». "
                            "Если вы являетесь жителем данного города и у вас нету доступа к этой команде, установите в настройках часовой пояс — Москва – UTC+3.</b>")
        return

    if not from_station_underground or not to_station_underground:
        await message.reply("🚇 <b>Маршрут следования не был установлен. "
                            "Пожалуйста, установите маршрут перед построением пути следования до конечной станции.</b>")
        return

    initial_message = await message.reply("🚇↔ <b>Строим маршрут следования к конечной станции...</b>")
    try:
        await message.delete()
    except Exception:
        pass

    last_update_time["underground"][user_id] = datetime.now()
    await update_underground(initial_message, user_id, state)
    await state.set_state()


@schedule.callback_query(lambda c: c.data == "manual_update_underground")
async def handle_manual_update_underground(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    now = datetime.now()

    last_time = last_update_time["underground"].get(user_id)
    if last_time and now - last_time < timedelta(minutes=1):
        await callback_query.answer("🔄 Подождите немного перед следующим обновлением.", show_alert=True)
        return

    last_update_time["underground"][user_id] = now
    await update_underground(callback_query.message, user_id, state)
    await callback_query.answer("🚇🔄 Маршрут обновлён.")


@schedule.callback_query(lambda c: c.data == "send_underground")
async def handle_send_underground(callback_query: types.CallbackQuery, state: FSMContext):
    await send_underground(callback_query.message, state)
    await callback_query.message.delete()


# Trains
async def update_trains(message: Message, user_id: int, state: FSMContext):
    data = await state.get_data()
    tz = timezone(data.get('timezone', 'Europe/Moscow'))

    from_city = data.get('from_city')
    to_city = data.get('to_city')
    current_time = datetime.now(tz).strftime('%H:%M')

    train_info = get_train_info(from_city, to_city, str(tz))
    train_image_selector = ImageSelector(train_urls)
    random_image = train_image_selector.get_random_image()

    if train_info:
        additional_text = f"\n🚂 <b>Последнее обновление в {current_time}. Вы можете обновить расписание вручную раз в минуту.</b>"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 | Обновить расписание", callback_data="manual_update_train")],
            [InlineKeyboardButton(text="🗑 | Удалить расписание", callback_data="delete_message")]
        ])
        train_info += additional_text
        media = InputMediaPhoto(media=random_image, caption=train_info)
        await message.edit_media(media, reply_markup=keyboard)
    else:
        await message.edit_text(
            "🚂🚫 <b>К сожалению, по вашему маршруту следования мы не нашли расписание. "
            "Пожалуйста, укажите действительный маршрут следования поезда дальнего следования.</b>"
        )


@schedule.message(Command('train'))
async def send_trains(message: Message, state: FSMContext):
    data = await state.get_data()
    from_city = data.get('from_city')
    to_city = data.get('to_city')
    user_id = message.chat.id

    if not from_city or not to_city:
        await message.reply("🚂🏙 <b>Маршрут следования не был установлен. "
                            "Пожалуйста, установите маршрут перед поиском расписания следования электричек.</b>")
        try:
            await message.delete()
        except Exception:
            pass
        return

    initial_message = await message.reply("🚂🗓 <b>Получаем расписание поездов дальнего следования...</b>")
    try:
        await message.delete()
    except Exception:
        pass

    last_update_time["train"][user_id] = datetime.now()
    await update_trains(initial_message, user_id, state)
    await state.set_state()


@schedule.callback_query(lambda c: c.data == "manual_update_train")
async def handle_manual_update_train(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    now = datetime.now()

    last_time = last_update_time["train"].get(user_id)
    if last_time and now - last_time < timedelta(minutes=1):
        await callback_query.answer("🔄 Подождите немного перед следующим обновлением.", show_alert=True)
        return

    last_update_time["train"][user_id] = now
    await update_trains(callback_query.message, user_id, state)
    await callback_query.answer("🚂🔄 Расписание обновлено.")


@schedule.callback_query(lambda c: c.data == "send_train")
async def handle_send_train(callback_query: types.CallbackQuery, state: FSMContext):
    await send_trains(callback_query.message, state)
    await callback_query.message.delete()


# Intercity Bus
async def update_intercity_bus(message: Message, user_id: int, state: FSMContext):
    data = await state.get_data()
    tz = timezone(data.get('timezone', 'Europe/Moscow'))

    from_city = data.get('from_city')
    to_city = data.get('to_city')
    current_time = datetime.now(tz).strftime('%H:%M')

    bus_info = get_intercity_bus_info(from_city, to_city, str(tz))
    bus_image_selector = ImageSelector(plane_urls)
    random_image = bus_image_selector.get_random_image()

    if bus_info:
        additional_text = f"\n🚐 <b>Последнее обновление в {current_time}. Вы можете обновить расписание вручную раз в минуту.</b>"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 | Обновить расписание", callback_data="manual_update_intercity_bus")],
            [InlineKeyboardButton(text="🗑 | Удалить расписание", callback_data="delete_message")]
        ])
        bus_info += additional_text
        media = InputMediaPhoto(media=random_image, caption=bus_info)
        await message.edit_media(media, reply_markup=keyboard)
    else:
        await message.edit_text(
            "🚐🚫 <b>К сожалению, по вашему маршруту следования мы не нашли расписание. "
            "Пожалуйста, укажите действительные города, для которых доступно расписание.</b>"
        )


@schedule.message(Command('intercitybus'))
async def send_intercity_bus(message: Message, state: FSMContext):
    data = await state.get_data()
    from_city = data.get('from_city')
    to_city = data.get('to_city')
    user_id = message.chat.id

    if not from_city or not to_city:
        await message.reply("🚐🏙 <b>Маршрут следования не был установлен. "
                            "Пожалуйста, установите маршрут перед поиском расписания автобусов.</b>")
        try:
            await message.delete()
        except Exception:
            pass
        return

    initial_message = await message.reply("🚐🗓 <b>Получаем расписание междугородних автобусов...</b>")
    try:
        await message.delete()
    except Exception:
        pass

    last_update_time["intercity_bus"][user_id] = datetime.now()
    await update_intercity_bus(initial_message, user_id, state)
    await state.set_state()


@schedule.callback_query(lambda c: c.data == "manual_update_intercity_bus")
async def handle_manual_update_intercity_bus(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    now = datetime.now()

    last_time = last_update_time["intercity_bus"].get(user_id)
    if last_time and now - last_time < timedelta(minutes=1):
        await callback_query.answer("🔄 Подождите немного перед следующим обновлением.", show_alert=True)
        return

    last_update_time["intercity_bus"][user_id] = now
    await update_intercity_bus(callback_query.message, user_id, state)
    await callback_query.answer("🚐🔄 Расписание обновлено.")


@schedule.callback_query(lambda c: c.data == "send_intercity_bus")
async def handle_send_intercity_bus(callback_query: types.CallbackQuery, state: FSMContext):
    await send_intercity_bus(callback_query.message, state)
    await callback_query.message.delete()


# Plane
async def update_planes(message: Message, user_id: int, state: FSMContext):
    data = await state.get_data()
    tz = timezone(data.get('timezone', 'Europe/Moscow'))

    from_city = data.get('from_city')
    to_city = data.get('to_city')
    current_time = datetime.now(tz).strftime('%H:%M')

    plane_info = get_plane_info(from_city, to_city, str(tz))
    plane_image_selector = ImageSelector(plane_urls)
    random_image = plane_image_selector.get_random_image()

    if plane_info:
        additional_text = f"\n🛫 <b>Последнее обновление в {current_time}. Вы можете обновить расписание вручную раз в минуту.</b>"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 | Обновить расписание", callback_data="manual_update_plane")],
            [InlineKeyboardButton(text="🗑 | Удалить расписание", callback_data="delete_message")]
        ])
        plane_info += additional_text
        media = InputMediaPhoto(media=random_image, caption=plane_info)
        await message.edit_media(media, reply_markup=keyboard)
    else:
        await message.edit_text(
            "🛫🚫 <b>К сожалению, по вашему маршруту следования мы не нашли расписание. "
            "Пожалуйста, укажите действительные города, для которых доступно расписание.</b>"
        )


@schedule.message(Command('plane'))
async def send_planes(message: Message, state: FSMContext):
    data = await state.get_data()
    from_city = data.get('from_city')
    to_city = data.get('to_city')
    user_id = message.chat.id

    if not from_city or not to_city:
        await message.reply("✈🏙 <b>Маршрут следования не был установлен. "
                            "Пожалуйста, установите маршрут перед поиском расписания самолётов.</b>")
        try:
            await message.delete()
        except Exception:
            pass
        return

    initial_message = await message.reply("✈🗓 <b>Получаем расписание самолётов...</b>")
    try:
        await message.delete()
    except Exception:
        pass

    last_update_time["plane"][user_id] = datetime.now()
    await update_planes(initial_message, user_id, state)
    await state.set_state()


@schedule.callback_query(lambda c: c.data == "manual_update_plane")
async def handle_manual_update_plane(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    now = datetime.now()

    last_time = last_update_time["plane"].get(user_id)
    if last_time and now - last_time < timedelta(minutes=1):
        await callback_query.answer("🔄 Подождите немного перед следующим обновлением.", show_alert=True)
        return

    last_update_time["plane"][user_id] = now
    await update_planes(callback_query.message, user_id, state)
    await callback_query.answer("✈🔄 Расписание обновлено.")


@schedule.callback_query(lambda c: c.data == "send_plane")
async def handle_send_plane(callback_query: types.CallbackQuery, state: FSMContext):
    await send_planes(callback_query.message, state)
    await callback_query.message.delete()
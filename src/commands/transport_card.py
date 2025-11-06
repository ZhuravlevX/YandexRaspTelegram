import asyncio
from datetime import datetime, timedelta

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, URLInputFile
from src.requests.get_token_authorization import get_new_access_token
from src.requests.get_transport_card_info import get_troika_info, get_transport_card_info
from src.utils.load_config import load_config

config = load_config()
transport_card = Router()

last_update_time = {
    "transport_card": {}
}


@transport_card.message(Command('troika'))
async def troika_search_handler(message: Message):
    parts = message.text.strip().split()
    invalid_card = len(parts) != 2 or not parts[1].isdigit() or len(parts[1]) != 10

    if invalid_card:
        temp_msg = await message.answer(
            '<b>💳🚫 Номер карты должен содержать ровно 10 цифр. Используйте команду следующим образом: <i>/troika 1234567890</i></b>')
        try:
            await message.delete()
        except Exception:
            pass
        await asyncio.sleep(15)
        try:
            await temp_msg.delete()
        except Exception:
            pass
        return

    try:
        await message.delete()
    except Exception:
        pass

    card_number = parts[1]
    temp_msg = await message.answer(
        "💳⌛ <b>Получаем информацию об транспортной карте и тарифах по указанному номеру...</b>")

    try:
        result, img = get_troika_info(card_number)
    except Exception:
        await temp_msg.edit_text(
            f'💳🚫 <b>Карта с номером {card_number} не найдена, либо она недоступна.</b>'
        )
        await asyncio.sleep(15)
        await temp_msg.delete()
        return

    if not result:
        await temp_msg.edit_text(
            f'💳🚫 <b>Карта с номером {card_number} не найдена, либо она недоступна.</b>'
        )
        await asyncio.sleep(15)
        await temp_msg.delete()
        return

    photo = URLInputFile(img, filename='troika.png')

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💸 | Пополнить",
                                  callback_data=f"topup_{card_number}"),
             InlineKeyboardButton(text="🎟 | Тарифы",
                                  callback_data=f"tariff_{card_number}")],
            [InlineKeyboardButton(text="🗑 | Удалить информацию", callback_data="delete_message")],
        ]
    )
    await temp_msg.edit_media(InputMediaPhoto(media=photo, caption=str(result)), reply_markup=keyboard)


@transport_card.message(Command("transportcard"))
async def transport_card_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.chat.id
    refresh_token = data.get("refresh_token")
    access_token = data.get("access_token")
    time_end_token = data.get("time_end_token")

    await message.delete()

    if not refresh_token:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📎 | Авторизоваться в личный кабинет",
                                      callback_data="authorize_transportcard")]
            ]
        )
        await message.answer(
            '👤ℹ <b>Для того, чтобы просматривать информацию об своих привязанных транспортных картах, необходимо авторизоваться по своему номеру телефона, '
            'к которому привязан ваш личный кабинет.</b>',
            reply_markup=keyboard
        )
    else:
        current_time = datetime.now().strftime('%H:%M')
        now = datetime.now()

        info_message = await message.answer("👤⌛ <b>Получаем данные транспортных карт с личного кабинета...</b>")

        if not time_end_token or time_end_token < now.timestamp():
            await info_message.edit_text(
                '👤🔄 <b>Обновляем авторизацию личного кабинета для получения транспортных карт... Пожалуйста подождите...</b>')
            new_access_token, time_sec = get_new_access_token(refresh_token)
            new_time_end_token = now + timedelta(seconds=time_sec - 300)
            await state.update_data(
                access_token=new_access_token,
                time_end_token=new_time_end_token.timestamp()
            )
            card_info = get_transport_card_info(new_access_token)
        else:
            card_info = get_transport_card_info(access_token)

        if card_info:
            additional_text = f"\n👤 <b>Последнее обновление в {current_time}. Вы можете обновить расписание вручную раз в минуту.</b>"
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 | Обновить информацию", callback_data="manual_update_transportcard")],
                [InlineKeyboardButton(text="🗑 | Удалить информацию", callback_data="delete_message")]
            ])
            card_info += additional_text
            last_update_time["transport_card"][user_id] = datetime.now()
            await info_message.edit_text(card_info, reply_markup=keyboard)
        else:
            await info_message.edit_text(
                "👤🚫 <b>К сожалению не удалось получить данные транспортных карт с личного кабинета. Возможно вы не привязали ни одну транспортную карту к личному кабинету.</b>"
            )


@transport_card.callback_query(lambda c: c.data == "manual_update_transportcard")
async def handle_manual_update_transport_card(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    now = datetime.now()

    last_time = last_update_time["transport_card"].get(user_id)
    if last_time and now - last_time < timedelta(minutes=1):
        await callback_query.answer("🔄 Подождите немного перед следующим обновлением.", show_alert=True)
        return

    last_update_time["transport_card"][user_id] = now
    await update_transport_card(callback_query.message, callback_query, user_id, state)
    await callback_query.answer("👤🔄 Данные транспортных карт с личного кабинета обновлены.")


async def update_transport_card(message: Message, callback_query: types.CallbackQuery, user_id: int, state: FSMContext):
    data = await state.get_data()
    refresh_token = data.get("refresh_token")
    current_time = datetime.now().strftime('%H:%M')
    access_token = data.get("access_token")
    time_end_token = data.get("time_end_token")
    now = datetime.now()

    if not refresh_token:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📎 | Авторизоваться в личный кабинет",
                                      callback_data="authorize_transportcard")]
            ]
        )
        await message.edit_text(
            '👤🚫 <b>К сожалению не удалось получить данные транспортных карт с личного кабинета. Возможно вы вышли из личного кабинета. '
            'Для того, чтобы просматривать информацию об своих привязанных транспортных картах, необходимо авторизоваться по своему номеру телефона, '
            'к которому привязан ваш личный кабинет.</b>',
            reply_markup=keyboard
        )

    if not time_end_token or time_end_token < now.timestamp():
        await callback_query.answer(
            '👤🔄 Обновляем авторизацию личного кабинета для получения транспортных карт... Пожалуйста подождите...')
        new_access_token, time_sec = get_new_access_token(refresh_token)
        new_time_end_token = now + timedelta(seconds=time_sec - 300)
        await state.update_data(
            access_token=new_access_token,
            time_end_token=new_time_end_token.timestamp()
        )
        card_info = get_transport_card_info(new_access_token)
    else:
        card_info = get_transport_card_info(access_token)

    if card_info:
        additional_text = f"\n👤 <b>Последнее обновление в {current_time}. Вы можете обновить информацию вручную раз в минуту.</b>"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 | Обновить информацию", callback_data="manual_update_transportcard")],
            [InlineKeyboardButton(text="🗑 | Удалить информацию", callback_data="delete_message")]
        ])
        card_info += additional_text
        await message.edit_text(card_info, reply_markup=keyboard)
    else:
        await message.edit_text(
            "👤🚫 <b>К сожалению не удалось получить данные транспортных карт с личного кабинета. "
            "Возможно вы не привязали ни одну транспортную карту к личному кабинету."
        )

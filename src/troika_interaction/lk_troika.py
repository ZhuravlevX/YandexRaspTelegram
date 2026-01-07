import asyncio
import os
from datetime import timedelta, datetime
import re

from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, \
    URLInputFile
import requests

from src.commands.transport_card import update_transport_card
from src.models.mosmetro.lk_response_troika import Card
from src.requests.get_token_authorization import get_new_access_token
from src.requests.get_transport_card_info import get_lk_troika_info
from src.utils.load_config import load_config

config = load_config()

TOP_UP_AMOUNTS = [10, 50, 100, 250, 500, 1000]

troika_lk = Router()

last_update_time = {
    "card_lk": {}
}

class TroikaStates(StatesGroup):
    waiting_manual_sum = State()
    waiting_payment = State()

@troika_lk.callback_query(lambda c: c.data.startswith("lktroika_"))
async def show_lk_troika_options(callback_query: CallbackQuery, state: FSMContext):
    linked_card = callback_query.data.split("_")[1]
    user_id = callback_query.message.chat.id

    data = await state.get_data()
    refresh_token = data.get("refresh_token")
    access_token = data.get("access_token")
    time_end_token = data.get("time_end_token")

    now = datetime.now()
    current_time = datetime.now().strftime('%H:%M')

    if not time_end_token or time_end_token < now.timestamp():
        new_access_token, time_sec = get_new_access_token(refresh_token)
        new_time_end_token = now + timedelta(seconds=time_sec - 300)
        await state.update_data(
            access_token=new_access_token,
            time_end_token=new_time_end_token.timestamp()
        )
        access_token = new_access_token

    card_info = get_lk_troika_info(linked_card, access_token)
    if card_info:
        lk_card, img = card_info
        additional_text = f"\n💳 <b>Последнее обновление в {current_time}. Вы можете обновить информацию вручную раз в минуту.</b>"
        last_update_time["card_lk"][user_id] = datetime.now()

        lk_card += additional_text

        response = requests.get(
            f"{os.getenv("BACKEND_URL")}{os.getenv("PORT")}/mosmetro/troika/transport_card/?access_token={access_token}&linked_card_id={linked_card}")
        lk_troika_data = Card(**response.json())

        buttons = []
        update_delete_buttons = [
            InlineKeyboardButton(text="🔄 | Обновить информацию", callback_data=f"lktransportcard_{linked_card}"),
            InlineKeyboardButton(text="🗑 | Удалить информацию", callback_data="delete_message")
        ]
        if lk_troika_data.status == 'action' and lk_troika_data.cardType == 'troika':
            buttons.extend([
                [InlineKeyboardButton(text="💸 | Пополнить", callback_data=f"lktopup_{linked_card}"),
                 InlineKeyboardButton(text="🎟 | Тарифы", callback_data=f"lktariff_{linked_card}")],
                [InlineKeyboardButton(text="🔒 | Заблокировать", callback_data=f"blocked_{linked_card}"),
                 InlineKeyboardButton(text="📎 | Отвязать", callback_data=f"unlinked_{linked_card}")]
            ])
        elif lk_troika_data.status == 'blocked':
            buttons.append([
                InlineKeyboardButton(text="🔓 | Разблокировать", callback_data=f"unblocked_{linked_card}")
            ])
        elif lk_troika_data.status == 'annulled' or lk_troika_data.cardType == 'social':
            buttons.append([
                InlineKeyboardButton(text="📎 | Отвязать", callback_data=f"unlinked_{linked_card}")
            ])
        if lk_troika_data.cardType in ['troika', 'blocked', 'social', 'annulled', 'virtual']:
            buttons.append(update_delete_buttons)
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        photo = URLInputFile(img, filename='troika.png')
        await callback_query.message.answer_photo(photo=photo, caption=lk_card, reply_markup=keyboard)
        await callback_query.answer()
    else:
        await callback_query.answer("💳🚫 Транспортная карта не найдена в личном кабинете. "
                                    "Возможно вы её отвязали, либо данная карта выбранная вами не была привязана к личному кабинету. "
                                    "Данные вашего личного кабинета были обновлены.",
                                    show_alert=True)
        await update_transport_card(callback_query.message, callback_query, state)


@troika_lk.callback_query(lambda c: c.data.startswith("lktransportcard_"))
async def handle_manual_update_lk_transport_card(callback_query: types.CallbackQuery, state: FSMContext):
    linked_card = callback_query.data.split("_")[1]

    user_id = callback_query.from_user.id
    now = datetime.now()

    last_time = last_update_time["card_lk"].get(user_id)
    if last_time and now - last_time < timedelta(minutes=1):
        await callback_query.answer("🔄 Подождите немного перед следующим обновлением.", show_alert=True)
        return

    last_update_time["card_lk"][user_id] = now
    await update_lk_transport_card(callback_query.message, callback_query, state, linked_card)
    await callback_query.answer("💳🔄 Данные транспортной карты с личного кабинета обновлены.")


async def update_lk_transport_card(message: Message, callback_query: types.CallbackQuery, state: FSMContext,
                                   linked_card):
    data = await state.get_data()
    refresh_token = data.get("refresh_token")
    current_time = datetime.now().strftime('%H:%M')
    access_token = data.get("access_token")
    time_end_token = data.get("time_end_token")
    now = datetime.now()

    if not refresh_token:
        await message.delete()
        await callback_query.answer(
            "💳🚫 К сожалению не удалось получить данные транспортной карты с личного кабинета. "
            "Возможно вы вышли из личного кабинета.", show_alert=True)
        return

    if not time_end_token or time_end_token < now.timestamp():
        await callback_query.answer(
            '👤🔄 Обновляем авторизацию личного кабинета для получения данных транспортной карты... Пожалуйста подождите...')
        new_access_token, time_sec = get_new_access_token(refresh_token)
        new_time_end_token = now + timedelta(seconds=time_sec - 300)
        await state.update_data(
            access_token=new_access_token,
            time_end_token=new_time_end_token.timestamp()
        )
        access_token = new_access_token

    card_info = get_lk_troika_info(linked_card, access_token)
    if card_info:
        lk_card, img = card_info
        response = requests.get(
            f"{os.getenv("BACKEND_URL")}{os.getenv("PORT")}/mosmetro/troika/transport_card/?access_token={access_token}&linked_card_id={linked_card}")
        lk_troika_data = Card(**response.json())

        buttons = []
        update_delete_buttons = [
            InlineKeyboardButton(text="🔄 | Обновить информацию", callback_data=f"lktransportcard_{linked_card}"),
            InlineKeyboardButton(text="🗑 | Удалить информацию", callback_data="delete_message")
        ]
        if lk_troika_data.status == 'action' and lk_troika_data.cardType == 'troika':
            buttons.extend([
                [InlineKeyboardButton(text="💸 | Пополнить", callback_data=f"lktopup_{linked_card}"),
                 InlineKeyboardButton(text="🎟 | Тарифы", callback_data=f"lktariff_{linked_card}")],
                [InlineKeyboardButton(text="🔒 | Заблокировать", callback_data=f"blocked_{linked_card}"),
                 InlineKeyboardButton(text="📎 | Отвязать", callback_data=f"unlinked_{linked_card}")]
            ])
        elif lk_troika_data.status == 'blocked':
            buttons.append([
                InlineKeyboardButton(text="🔓 | Разблокировать", callback_data=f"unblocked_{linked_card}")
            ])
        elif lk_troika_data.status == 'annulled' or lk_troika_data.cardType == 'social':
            buttons.append([
                InlineKeyboardButton(text="📎 | Отвязать", callback_data=f"unlinked_{linked_card}")
            ])
        if lk_troika_data.cardType in ['troika', 'blocked', 'social', 'annulled', 'virtual']:
            buttons.append(update_delete_buttons)
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        additional_text = f"\n💳 <b>Последнее обновление в {current_time}. Вы можете обновить информацию вручную раз в минуту.</b>"
        lk_card += additional_text
        photo = URLInputFile(img, filename='troika.png')
        media = InputMediaPhoto(media=photo, caption=lk_card)
        await message.bot.edit_message_media(chat_id=message.chat.id, message_id=message.message_id,
                                             reply_markup=keyboard, media=media)
    else:
        await message.delete()
        await callback_query.answer(
            "💳🚫 К сожалению не удалось получить данные транспортной карты с личного кабинета. "
            "Данная карта не найдена.", show_alert=True)

@troika_lk.callback_query(lambda c: c.data.startswith("lktopup_"))
async def show_topup_options(callback_query: CallbackQuery):
    linked_card = callback_query.data.split("_")[1]
    buttons = [
        [InlineKeyboardButton(text=f"💵 | Пополнить на {amount} рублей",
                              callback_data=f"lkchoosepay_{linked_card}_{amount}_4414")]
        for amount in TOP_UP_AMOUNTS
    ]
    buttons.append([InlineKeyboardButton(text="💷 | Пополнить на свою сумму", callback_data=f"lkmanualsum_{linked_card}")])
    buttons.append([InlineKeyboardButton(text="⬅️ | Назад", callback_data=f"back_to_linked_{linked_card}")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)

@troika_lk.callback_query(lambda c: c.data.startswith("lktariff_"))
async def show_tariff_options(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    refresh_token = data.get("refresh_token")
    access_token = data.get("access_token")
    time_end_token = data.get("time_end_token")

    now = datetime.now()

    if not time_end_token or time_end_token < now.timestamp():
        new_access_token, time_sec = get_new_access_token(refresh_token)
        new_time_end_token = now + timedelta(seconds=time_sec - 300)
        await state.update_data(
            access_token=new_access_token,
            time_end_token=new_time_end_token.timestamp()
        )
        access_token = new_access_token

    linked_card = callback_query.data.split("_")[1]
    response = requests.get(
        f"{os.getenv("BACKEND_URL")}{os.getenv("PORT")}/mosmetro/troika/transport_card/?access_token={access_token}&linked_card_id={linked_card}")
    lk_troika_data = Card(**response.json())
    products = lk_troika_data.availableProducts

    buttons = []
    for product in products:
        button_text = f"🧾 | {re.sub(r'\s{2,}', ' ', product.name.strip())} за {product.price} рублей"
        buttons.append([InlineKeyboardButton(text=button_text,
                                             callback_data=f"choosepay_{linked_card}_{product.price}_{product.id}")])
    buttons.append([InlineKeyboardButton(text="⬅️ | Назад", callback_data=f"back_to_linked_{linked_card}")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)

@troika_lk.callback_query(lambda c: c.data.startswith("lkchoosepay_"))
async def choose_payment_type(callback_query: CallbackQuery):
    _, linked_card, payment_sum, product_id = callback_query.data.split("_")
    payment_sum = int(payment_sum)
    product_id = int(product_id)
    if product_id == 4414:
        callback_button = f'lktopup_{linked_card}'
    else:
        callback_button = f'lktariff_{linked_card}'

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏦 | Банковская карта",
                                     callback_data=f"lkpay_{linked_card}_{payment_sum}_{product_id}_bankCard"),
                InlineKeyboardButton(text="💠 | Система Быстрых Платежей",
                                     callback_data=f"lkpay_{linked_card}_{payment_sum}_{product_id}_sbp")
            ],
            [InlineKeyboardButton(text="⬅️ | Назад", callback_data=callback_button)]
        ]
    )
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)

@troika_lk.callback_query(lambda c: c.data.startswith("lkpay_"))
async def process_payment(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    refresh_token = data.get("refresh_token")
    access_token = data.get("access_token")
    time_end_token = data.get("time_end_token")

    now = datetime.now()

    if not time_end_token or time_end_token < now.timestamp():
        new_access_token, time_sec = get_new_access_token(refresh_token)
        new_time_end_token = now + timedelta(seconds=time_sec - 300)
        await state.update_data(
            access_token=new_access_token,
            time_end_token=new_time_end_token.timestamp()
        )
        access_token = new_access_token

    _, linked_card, payment_sum, product_id, payment_type = callback_query.data.split("_")
    payment_sum = int(payment_sum)

    payload = {
        "callbackUrl": "mosmetro://redirect/payment",
        "linkedCardId": linked_card,
        "paymentSum": payment_sum,
        "paymentType": payment_type,
        "saleType": "prepaid",
        "ticketId": product_id
    }

    headers = {
        "User-Agent": "MosMetro/4.2.3 (7874) (Android; samsung SM-A155F; 15; 2629830780)",
        "Authorization": f"Bearer {access_token}"
    }

    payment_response = requests.post("https://lk.mosmetro.ru/api/payments/v1.0", json=payload, headers=headers)
    if payment_response.ok and not await state.get_state() == TroikaStates.waiting_payment:
        data = payment_response.json().get("data", {})
        authorize_url = data.get("authorizeUrl")
        session_id = data.get("sessionId")

        await state.set_state(TroikaStates.waiting_payment)

        if authorize_url and session_id:
            pay_keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=f"💱 | Оплатить {payment_sum} рублей", url=authorize_url)],
                    [InlineKeyboardButton(text="🚫 | Отменить платёжную операцию",
                                          callback_data=f"back_to_linked_{linked_card}")]
                ],
            )
            await callback_query.message.edit_reply_markup(reply_markup=pay_keyboard)

            while True:
                await asyncio.sleep(15)
                check_response = requests.get(f"https://lk.mosmetro.ru/api/payments/v1.0/{session_id}", headers=headers)

                if check_response.ok and await state.get_state() == TroikaStates.waiting_payment:
                    check_data = check_response.json().get("data", {})
                    status = check_data.get("status")
                    if status == "success":
                        await callback_query.message.answer(
                            f"💳✅ <b>Транспортная карта «Тройка» получила платёж на сумму {payment_sum} рублей. "
                            f"Чтобы активировать пополнение или тариф, воспользуйтесь турникетом в «Московском Метрополитене», "
                            f"валидатором в наземном транспорте, а также автоматом для продажи билетов.</b>",
                            show_alert=True)
                        await state.set_state(None)
                        await update_lk_transport_card(callback_query.message, callback_query, state, linked_card)
                        break
                    if status == "failed":
                        await callback_query.message.answer(
                            f"💵🚫 <b>Транспортная карта «Тройка» не получила платёж на сумму {payment_sum} рублей. "
                            f"Пополнение или приобретение тарифа на данную транспортную карту не осуществлен. </b>",
                            show_alert=True)
                        await state.set_state(None)
                        await update_lk_transport_card(callback_query.message, callback_query, state, linked_card)
                        break
                else:
                    break
    else:
        await callback_query.answer('💳⚠ На текущий момент у вас активна другая оплата для транспортной карты. '
                                  'Пожалуйста завершите либо отмените её перед тем, как начать новую оплату.', show_alert=True)

@troika_lk.callback_query(lambda c: c.data.startswith("back_to_linked_"))
async def back_to_card_view(callback_query: CallbackQuery, state: FSMContext):
    linked_card = callback_query.data.split("_")[-1]
    await state.set_state(None)
    await update_lk_transport_card(callback_query.message, callback_query, state, linked_card)


@troika_lk.callback_query(lambda c: c.data.startswith("blocked_"))
async def handle_block_transport_card(callback_query: types.CallbackQuery, state: FSMContext):
    linked_card = callback_query.data.split("_")[1]

    data = await state.get_data()
    refresh_token = data.get("refresh_token")
    access_token = data.get("access_token")
    time_end_token = data.get("time_end_token")

    now = datetime.now()

    if not time_end_token or time_end_token < now.timestamp():
        new_access_token, time_sec = get_new_access_token(refresh_token)
        new_time_end_token = now + timedelta(seconds=time_sec - 300)
        await state.update_data(
            access_token=new_access_token,
            time_end_token=new_time_end_token.timestamp()
        )
        access_token = new_access_token

    headers = {
        "Authorization": f"Bearer {access_token}",
        "User-Agent": "MosMetro/4.2.3 (7874) (Android; samsung SM-A155F; 15; 2629830780)"
    }

    response = requests.put(f"{os.getenv("LK_MOSMETRO_API_URL")}/carriers/v1.0/{linked_card}/block?block=true",
                            headers=headers)
    print(response.text)

    await update_lk_transport_card(callback_query.message, callback_query, state, linked_card)
    await callback_query.answer("💳🔒 Транспортная карта заблокирована.")


@troika_lk.callback_query(lambda c: c.data.startswith("unblocked_"))
async def handle_unblock_transport_card(callback_query: types.CallbackQuery, state: FSMContext):
    linked_card = callback_query.data.split("_")[1]

    data = await state.get_data()
    refresh_token = data.get("refresh_token")
    access_token = data.get("access_token")
    time_end_token = data.get("time_end_token")

    now = datetime.now()

    if not time_end_token or time_end_token < now.timestamp():
        new_access_token, time_sec = get_new_access_token(refresh_token)
        new_time_end_token = now + timedelta(seconds=time_sec - 300)
        await state.update_data(
            access_token=new_access_token,
            time_end_token=new_time_end_token.timestamp()
        )
        access_token = new_access_token

    headers = {
        "Authorization": f"Bearer {access_token}",
        "User-Agent": "MosMetro/4.2.3 (7874) (Android; samsung SM-A155F; 15; 2629830780)"
    }

    response = requests.put(f"{os.getenv("LK_MOSMETRO_API_URL")}/carriers/v1.0/{linked_card}/unblock", headers=headers)
    print(response.text)

    await update_lk_transport_card(callback_query.message, callback_query, state, linked_card)
    await callback_query.answer("💳🔓 Транспортная карта разблокирована.")


@troika_lk.callback_query(lambda c: c.data.startswith("unlinked_"))
async def handle_unlinked_transport_card(callback_query: types.CallbackQuery, state: FSMContext):
    linked_card = callback_query.data.split("_")[1]

    data = await state.get_data()
    refresh_token = data.get("refresh_token")
    access_token = data.get("access_token")
    time_end_token = data.get("time_end_token")

    now = datetime.now()

    if not time_end_token or time_end_token < now.timestamp():
        new_access_token, time_sec = get_new_access_token(refresh_token)
        new_time_end_token = now + timedelta(seconds=time_sec - 300)
        await state.update_data(
            access_token=new_access_token,
            time_end_token=new_time_end_token.timestamp()
        )
        access_token = new_access_token

    headers = {
        "Authorization": f"Bearer {access_token}",
        "User-Agent": "MosMetro/4.2.3 (7874) (Android; samsung SM-A155F; 15; 2629830780)"
    }

    response = requests.delete(f"{os.getenv("LK_MOSMETRO_API_URL")}/carriers/v1.0/{linked_card}", headers=headers)
    print(response.text)

    await callback_query.message.delete()
    await callback_query.answer("💳📎 Транспортная карта отвязана от личного кабинета. "
                                "Теперь вы не можете получать информацию данной транспортной карты.", show_alert=True)

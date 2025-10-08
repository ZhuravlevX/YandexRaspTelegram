import asyncio
import os

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, \
    URLInputFile
import requests

from src.models.mosmetro.search_response_troika import Troika
from src.requests.get_token_authorization import get_new_access_token
from src.requests.get_transport_card_info import get_troika_info
from src.utils.load_config import load_config

config = load_config()

TOP_UP_AMOUNTS = [10, 50, 100, 250, 500, 1000]

troika_pay = Router()


class TroikaStates(StatesGroup):
    waiting_manual_sum = State()


@troika_pay.callback_query(lambda c: c.data.startswith("topup_"))
async def show_topup_options(callback_query: CallbackQuery):
    card_number = callback_query.data.split("_")[1]
    buttons = [
        [InlineKeyboardButton(text=f"💵 | Пополнить на {amount} рублей",
                              callback_data=f"choosepay_{card_number}_{amount}_4414")]
        for amount in TOP_UP_AMOUNTS
    ]
    buttons.append([InlineKeyboardButton(text="💷 | Пополнить на свою сумму", callback_data=f"manualsum_{card_number}")])
    buttons.append([InlineKeyboardButton(text="⬅️ | Назад", callback_data=f"back_to_card_{card_number}")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)


@troika_pay.callback_query(lambda c: c.data.startswith("tariff_"))
async def show_tariff_options(callback_query: CallbackQuery):
    card_number = callback_query.data.split("_")[1]
    response = requests.get(f"{os.getenv('BACKEND_URL')}{os.getenv('PORT')}/mosmetro/troika/card_number/{card_number}")
    troika_data = Troika(**response.json())
    products = troika_data.availableProducts

    buttons = []
    for product in products:
        button_text = f"🧾 | {product.name} за {product.price} рублей"
        buttons.append([InlineKeyboardButton(text=button_text,
                                             callback_data=f"choosepay_{card_number}_{product.price}_{product.id}")])
    buttons.append([InlineKeyboardButton(text="⬅️ | Назад", callback_data=f"back_to_card_{card_number}")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)


@troika_pay.callback_query(lambda c: c.data.startswith("manualsum_"))
async def start_manual_input(callback_query: CallbackQuery, state: FSMContext):
    card_number = callback_query.data.split("_")[1]
    msg = await callback_query.message.answer(
        "<b>💳ℹ Сумма пополнения должна быть от 10 до 5000 рублей. Введите пожалуйста сумму пополнения.</b>"
    )
    await state.update_data(
        card_number=card_number,
        manual_prompt_id=msg.message_id,
        manual_markup_id=callback_query.message.message_id
    )
    await state.set_state(TroikaStates.waiting_manual_sum)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚫 | Отменить действие", callback_data=f"cancelmanual_{card_number}")]
        ]
    )
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)


@troika_pay.message(TroikaStates.waiting_manual_sum)
async def handle_manual_sum(message: Message, state: FSMContext):
    data = await state.get_data()
    card_number = data.get("card_number")
    prompt_id = data.get("manual_prompt_id")
    markup_id = data.get("manual_markup_id")
    try:
        sum_value = int(message.text.strip())
    except Exception:
        sum_value = None
    if not sum_value or sum_value < 10 or sum_value > 5000:
        warn = await message.answer(
            "<b>💳🚫 Сумма пополнения должна быть от 10 до 5000 рублей. Введите пожалуйста корректное значение.</b>")
        await asyncio.sleep(15)
        try:
            await warn.delete()
            print("!")
            await message.delete()
        except Exception:
            pass
        return
    try:
        await message.delete()
        await message.bot.delete_message(message.chat.id, prompt_id)
    except Exception:
        pass

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏦 | Банковская карта",
                                     callback_data=f"pay_{card_number}_{sum_value}_4414_bankCard"),
                InlineKeyboardButton(text="💠 | Система Быстрых Платежей",
                                     callback_data=f"pay_{card_number}_{sum_value}_4414_sbp")
            ],
            [InlineKeyboardButton(text="⬅️ | Назад", callback_data=f"topup_{card_number}")]
        ]
    )
    await state.update_data(manual_sum=sum_value)
    await state.set_state(None)
    await message.bot.edit_message_reply_markup(
        chat_id=message.chat.id,
        message_id=markup_id,
        reply_markup=keyboard
    )


@troika_pay.callback_query(lambda c: c.data.startswith("cancelmanual_"))
async def cancel_manual_input(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    prompt_id = data.get("manual_prompt_id")
    try:
        await callback_query.message.bot.delete_message(callback_query.message.chat.id, prompt_id)
    except Exception:
        pass
    await show_topup_options(callback_query)
    await state.set_state(None)


@troika_pay.callback_query(lambda c: c.data.startswith("choosepay_"))
async def choose_payment_type(callback_query: CallbackQuery):
    _, card_number, payment_sum, product_id = callback_query.data.split("_")
    payment_sum = int(payment_sum)
    product_id = int(product_id)
    if product_id == 4414:
        callback_button = f'topup_{card_number}'
    else:
        callback_button = f'tariff_{card_number}'

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏦 | Банковская карта",
                                     callback_data=f"pay_{card_number}_{payment_sum}_{product_id}_bankCard"),
                InlineKeyboardButton(text="💠 | Система Быстрых Платежей",
                                     callback_data=f"pay_{card_number}_{payment_sum}_{product_id}_sbp")
            ],
            [InlineKeyboardButton(text="⬅️ | Назад", callback_data=callback_button)]
        ]
    )
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)


@troika_pay.callback_query(lambda c: c.data.startswith("pay_"))
async def process_payment(callback_query: CallbackQuery, state: FSMContext):
    _, card_number, payment_sum, product_id, payment_type = callback_query.data.split("_")
    payment_sum = int(payment_sum)

    response = requests.get(f"{os.getenv('BACKEND_URL')}{os.getenv('PORT')}/mosmetro/troika/card_number/{card_number}")
    if not response.ok:
        return
    troika_data = Troika(**response.json())
    card_number_data = troika_data.card.cardNumber
    linked_card_id = troika_data.card.uid

    data = await state.get_data()
    refresh_token = data.get("refresh_token")
    if refresh_token:
        access_token, refresh_token = get_new_access_token(refresh_token)
        await state.update_data(
            access_token=access_token,
            refresh_token=refresh_token
        )
    else:
        access_token = None

    payload = {
        "callbackUrl": "mosmetro://redirect/payment",
        "cardUid": linked_card_id,
        "paymentSum": payment_sum,
        "paymentType": payment_type,
        "saleType": "prepaid",
        "ticketId": product_id
    }
    print(payload)
    headers = {
        "User-Agent": "MosMetro/4.2.3 (7874) (Android; samsung SM-A155F; 15; 2629830780)",
        "Authorization": f"Bearer {access_token}"
    }

    payment_response = requests.post("https://lk.mosmetro.ru/api/payments/v1.0", json=payload, headers=headers)
    if payment_response.ok:
        data = payment_response.json().get("data", {})
        authorize_url = data.get("authorizeUrl")
        session_id = data.get("sessionId")
        if authorize_url and session_id:
            pay_keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=f"💱 | Оплатить {payment_sum} рублей", url=authorize_url)],
                    [InlineKeyboardButton(text="🚫 | Отменить платёжную операцию",
                                          callback_data=f"back_to_card_{card_number}")]
                ],
            )
            await callback_query.message.edit_reply_markup(reply_markup=pay_keyboard)

            while True:
                await asyncio.sleep(15)
                check_response = requests.get(f"https://lk.mosmetro.ru/api/payments/v1.0/{session_id}", headers=headers)

                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="💸 | Пополнить",
                                              callback_data=f"topup_{card_number}"),
                         InlineKeyboardButton(text="🎟 | Тарифы",
                                              callback_data=f"tariff_{card_number}")],
                        [InlineKeyboardButton(text="🗑 | Удалить информацию", callback_data="delete_message")],
                    ]
                )

                if check_response.ok:
                    check_data = check_response.json().get("data", {})
                    status = check_data.get("status")
                    if status == "success":
                        await callback_query.message.answer(
                            f"💳✅ <b>Транспортная карта «Тройка» {card_number_data} получила платёж на сумму {payment_sum} рублей. "
                            f"Чтобы активировать пополнение или тариф, воспользуйтесь турникетом в «Московском Метрополитене», "
                            f"валидатором в наземном транспорте, а также автоматом для продажи билетов.</b>",
                            show_alert=True)
                        await callback_query.message.edit_reply_markup(reply_markup=keyboard)
                        break
                    if status == "failed":
                        await callback_query.message.answer(
                            f"💵🚫 <b>Транспортная карта «Тройка» {card_number_data} не получила платёж на сумму {payment_sum} рублей. "
                            f"Пополнение или приобретение тарифа на данную транспортную карту не осуществлен. </b>",
                            show_alert=True)
                        await callback_query.message.edit_reply_markup(reply_markup=keyboard)
                        break
    else:
        if not refresh_token:
            error_msg = await callback_query.message.answer(
                f"💱🚫 <b>На текущий момент, способ оплаты неактивен и не отвечает с стороны сервера. "
                f"Пожалуйста попробуйте позднее произвести данную операцию.</b>",
                show_alert=True)
            await asyncio.sleep(15)
            await error_msg.delete()
        # else:
        #     get_new_access_token(refresh_token)


# @troika_pay.callback_query(lambda c: c.data.startswith("checkpay_"))
# async def check_payment_status(callback_query: CallbackQuery, state: FSMContext):
#     _, session_id, payment_sum, card_number_data = callback_query.data.split("_")
#     payment_sum = int(payment_sum)
#
#     data = await state.get_data()
#     card_number = data.get("card_number")
#
#     headers = {
#         "User-Agent": "MosMetro/4.2.3 (7874) (Android; samsung SM-A155F; 15; 2629830780)",
#         "Authorization": f"Bearer 112C410BC363F45A5E55033BD8030BB8CA42F587F961E938D59BE190C86763B0"
#     }
#
#     response = requests.get(f"https://lk.mosmetro.ru/api/payments/v1.0/{session_id}", headers=headers)
#     if response.ok:
#         data = response.json().get("data", {})
#         status = data.get("status")
#         if status == "success":
#             await callback_query.message.answer(f"💳✅ <b>Карта {card_number_data} была успешно пополнена на {payment_sum} рублей! "
#                                                 f"Чтобы активировать пополнение, воспользуйтесь турникетом в «Московском Метрополитене», "
#                                                 f"валидатором в наземном транспорте, а также автоматом для продажи билетов.</b>", show_alert=True)
#             keyboard = InlineKeyboardMarkup(
#                 inline_keyboard=[
#                     [InlineKeyboardButton(text="💰 | Пополнить баланс", callback_data=f"topup_{card_number}")]
#                 ]
#             )
#             await callback_query.message.edit_reply_markup(reply_markup=keyboard)
#         else:
#             warn_msg = await callback_query.message.answer(
#                 f"💳❌ <b>На карту {card_number_data} не поступал платёж на сумму {payment_sum} рублей. "
#                 "Оплатите пополнение либо дождитесь обработки записи оплаты.</b>",
#                 show_alert=True
#             )
#             await asyncio.sleep(15)
#             try:
#                 await warn_msg.delete()
#             except Exception:
#                 pass
#     else:
#         print(response)

@troika_pay.callback_query(lambda c: c.data.startswith("back_to_card_"))
async def back_to_card_view(callback_query: CallbackQuery):
    card_number = callback_query.data.split("_")[-1]
    result, img = get_troika_info(card_number)
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
    await callback_query.message.edit_media(
        InputMediaPhoto(
            media=photo,
            caption=str(result)
        ),
        reply_markup=keyboard
    )

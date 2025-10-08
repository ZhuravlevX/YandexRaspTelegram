import asyncio
import os

from aiogram import Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
import requests

from src.utils.load_config import load_config

config = load_config()
TOP_UP_AMOUNTS = [10, 50, 100, 250, 500, 1000]

troika_auth = Router()


class TransportCardAuth(StatesGroup):
    waiting_for_phone = State()
    waiting_for_code = State()


def format_phone_number(phone: str) -> str:
    digits = ''.join(filter(str.isdigit, phone))
    if len(digits) == 11 and digits.startswith("7"):
        return f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
    return phone


@troika_auth.message(TransportCardAuth.waiting_for_phone)
async def process_phone_number(message: Message, state: FSMContext, bot: Bot):
    phone = message.text.strip()

    if phone.startswith("+") or not phone[10:].isdigit():
        warn = await message.answer(
            "📱🚫 <b>Пожалуйста, введите корректный номер телефона по численности и без плюса.</b>")
        await asyncio.sleep(15)
        try:
            await warn.delete()
            await message.delete()
        except Exception:
            pass
        return

    payload = {
        "username": phone,
        "scope": "openid offline_access nbs.ppa idps phone email all"
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {os.getenv("AUTHORIZATION_BASIC")}",
        "User-Agent": "MosMetro/4.2.3 (7874) (Android; samsung SM-A155F; 15; 2629830780)"
    }

    try:
        response = requests.post("https://auth.mosmetro.ru/connect/otp", data=payload, headers=headers)
        response.raise_for_status()
    except requests.RequestException:
        warn = await message.answer("📱🚫 <b>Номер телефона недоступен. "
                                    "Возможно по этому номеру телефона производят вход в личный кабинет, либо такого номера не существует."
                                    "Пожалуйста введите корректный или другой номер телефон.</b>")
        await asyncio.sleep(15)
        try:
            await warn.delete()
            await message.delete()
        except Exception:
            pass
        return

    otp_key = response.json().get("key")
    await state.update_data(phone_number=phone, otp_key=otp_key)

    try:
        await message.delete()
    except Exception:
        pass

    formatted_phone = format_phone_number(phone)

    data = await state.get_data()
    auth_message_id = data.get("auth_message_id")
    if auth_message_id:
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=auth_message_id,
            text=f"📲ℹ <b>На номер {formatted_phone} отправлен 6-ти значный код. Для завершения авторизации продублируйте его. Код действует в течении 5-ти минут.</b>",
            parse_mode="HTML"
        )

    await state.set_state(TransportCardAuth.waiting_for_code)
    await asyncio.sleep(300)
    current_state = await state.get_state()
    if current_state == TransportCardAuth.waiting_for_code:
        data = await state.get_data()
        auth_message_id = data.get("auth_message_id")
        if auth_message_id:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="📎 | Повторить попытку авторизовации",
                                          callback_data="authorize_transportcard")]
                ]
            )
            try:
                await bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=auth_message_id,
                    text="⏱️🚫 <b>Время срока действия 6-ти значного кода закончилось. Пожалуйста начните авторизацию сначала.</b>",
                    reply_markup=keyboard
                )
                await state.set_state(None)
            except Exception:
                pass
        await state.set_state(None)


@troika_auth.message(TransportCardAuth.waiting_for_code)
async def process_sms_code(message: Message, state: FSMContext, bot: Bot):
    code = message.text.strip()

    if not code.isdigit() or len(code) != 6:
        warn = await message.answer("📲🚫 <b>Пожалуйста, введите корректный 6-ти значный код.</b>", parse_mode="HTML")
        await asyncio.sleep(15)
        try:
            await warn.delete()
            await message.delete()
        except Exception:
            pass
        return

    data = await state.get_data()
    otp_key = data.get("otp_key")
    attempts = data.get("code_attempts", 0)

    payload = {
        "grant_type": "otp",
        "key": otp_key,
        "password": code
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {os.getenv("AUTHORIZATION_BASIC")}",
        "User-Agent": "MosMetro/4.2.3 (7874) (Android; samsung SM-A155F; 15; 2629830780)"
    }

    try:
        response = requests.post("https://auth.mosmetro.ru/connect/token", data=payload, headers=headers)
        response.raise_for_status()
        token_data = response.json()
    except requests.RequestException:
        attempts += 1
        await state.update_data(code_attempts=attempts)

        if attempts >= 5:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="📎 | Повторить попытку авторизации",
                                          callback_data="authorize_transportcard")]
                ]
            )
            data = await state.get_data()
            auth_message_id = data.get("auth_message_id")

            try:
                await bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=auth_message_id,
                    text="📩🚫 <b>Превышен лимит попыток. Пожалуйста начните авторизацию сначала.</b>",
                    reply_markup=keyboard
                )
            except Exception:
                pass

            await state.set_state(None)
            await state.update_data(code_attempts=0)

        else:
            warn = await message.answer("📲🚫 <b>Неверный 6-ти значный код. Пожалуйста введите правильный код.</b>")
            await asyncio.sleep(15)
            try:
                await warn.delete()
                await message.delete()
            except Exception:
                pass
        return

    refresh_token = token_data.get("refresh_token")
    await state.update_data(refresh_token=refresh_token, code_attempts=0)

    auth_message_id = data.get("auth_message_id")
    if auth_message_id:
        try:
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=auth_message_id,
                text="👤✅ <b>Вы авторизовались в свой личный кабинет. Теперь вы можете просматривать информацию об своих привязанных транспортных картах.</b>"
            )
            await message.delete()
        except Exception:
            pass
        await state.update_data(auth_message_id=None)
    await state.set_state(None)


@troika_auth.callback_query(lambda c: c.data == "authorize_transportcard")
async def authorize_transportcard_callback(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state in [TransportCardAuth.waiting_for_code, TransportCardAuth.waiting_for_phone]:
        warn = await callback.message.edit_text(
            "👤🚫 <b>На текущий момент вы уже начали процесс авторизации. Пожалуйста, завершите его.</b>"
        )
        await asyncio.sleep(15)
        try:
            await warn.delete()
        except Exception:
            pass
        return
    else:
        await state.update_data(auth_message_id=callback.message.message_id)
        await callback.message.edit_text(
            "📱ℹ <b>Введите свой номер телефона без плюса, к которому привязан ваш личный кабинет. Авторизация производится по номерам Российской Федерации.</b>"
        )
        await state.set_state(TransportCardAuth.waiting_for_phone)

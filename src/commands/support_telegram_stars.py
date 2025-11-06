import asyncio
import logging

from aiogram import types, F, Router
from aiogram.filters.command import Command
from aiogram.types import LabeledPrice, PreCheckoutQuery

support = Router()


@support.callback_query(lambda c: c.data == "support_developer")
async def handle_support_callback(callback_query: types.CallbackQuery):
    sent_message = await callback_query.send_message(
        chat_id=callback_query.message.chat.id,
        text=(
            '<b>⭐ℹ Если вы хотите, чтобы разработчику было приятно, вы можете поддержать его Telegram Stars! '
            'Заранее благодарим тех, кто решился нас поддержать! Для того, чтобы поддержать автора, пропишите команду: '
            '<i>/support "ЧИСЛО ОТ 1 ДО 5000"</i></b>'
        ),
    )
    await asyncio.sleep(15)
    await callback_query.delete_message(chat_id=sent_message.chat.id, message_id=sent_message.message_id)


@support.message(Command('support'))
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
    bot_msg = await message.send_invoice(
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
        await message.delete_message(chat_id=message.chat.id, message_id=bot_msg.message_id)
    except Exception:
        pass


@support.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@support.message(F.successful_payment)
async def process_successful_payment(message: types.Message):
    await message.send_message(chat_id=message.chat.id,
                               text='<b>⭐❤ Спасибо вам, что вы поддержали разработчика! Этим действием вы даете понять, что вы цените чужой труд!</b>',
                               message_effect_id="5159385139981059251")
    logging.info(f"Telegram Stars successful payment: {message.successful_payment.telegram_payment_charge_id}")

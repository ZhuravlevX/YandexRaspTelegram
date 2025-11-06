import logging
import os

from pytz import timezone
from datetime import datetime

from aiogram import types, Router, Bot
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

debug = Router()


# @dp.message(Command('log'))
# async def send_log_file(message: Message, state: FSMContext):
#     data = await state.get_data()
#     debug_menu = data.get('debug_menu')
#     if debug_menu:
#         log_file_path = '../YandexRaspBot-error.log'
#         if os.path.exists(log_file_path):
#             await message.answer_document(FSInputFile(log_file_path),
#                                           caption="✅⚙ <b>Файл логов был найден, отправляю его вам! Чтобы снова вызвать и получить логи, также воспользуйтесь командой /log.</b>")
#         else:
#             await message.answer(
#                 "❌⚙ <b>Файл логов не был найден. Скорее всего его не существует в текущей директории сервера.</b>")
#     else:
#         await state.update_data(debug_menu=False)


@debug.message(Command('refund'))
async def command_refund_handler(message: types.Message, state: FSMContext, bot: Bot):
    parts = message.text.strip().split()
    data = await state.get_data()
    debug_menu = data.get('debug_menu')
    if debug_menu:
        if len(parts) < 2:
            await message.answer("<b>ℹ Пожалуйста, укажите ID транзакции.</b>")
            return

        transaction_id = parts[1]
        try:
            await message.delete()
            await bot.refund_star_payment(
                user_id=message.from_user.id,
                telegram_payment_charge_id=transaction_id)
            logging.info(f"Telegram Stars refund request completed: {transaction_id}")
        except Exception as e:
            logging.info(f"Error when returning Telegram Stars: {e}")
    else:
        await state.update_data(debug_menu=False)


@debug.message(Command('requests_url'))
async def send_requests_url(message: Message, state: FSMContext):
    data = await state.get_data()
    date = datetime.now().strftime('%Y-%m-%d')
    from_city = data.get('from_city')
    to_city = data.get('to_city')

    from_station = data.get('from_station')
    to_station = data.get('to_station')

    tz = timezone(data.get('timezone', 'Europe/Moscow'))

    suburban_url = f"{os.getenv('YANDEX_API_URL')}/search?apikey={os.getenv('TOKEN_YANDEX')}&from={from_station}&to={to_station}&lang=ru_RU&date={date}&result_timezone={tz}&transport_types=suburban&limit=250"
    train_url = f"{os.getenv('YANDEX_API_URL')}/search?apikey={os.getenv('TOKEN_YANDEX')}&from={from_city}&to={to_city}&lang=ru_RU&date={date}&result_timezone={tz}&transport_types=train&limit=250"

    debug_menu = data.get('debug_menu')
    if debug_menu:
        await message.answer("✅🔗 <b>Вот ссылки API запросов для тестирования в Postman.\n\n</b>"
                             f"🚆 <b>API запрос пригородных поездов с выбранными вами станциями: {suburban_url}\n\n</b>"
                             f"🚂 <b>API запрос поездов дальнего следования с выбранными вами городами: {train_url}\n\n</b>"
                             "<b>Для просмотра информации из данных API, требуется зайти на https://www.postman.com/ и вставить туда ссылку либо открыть ссылку в браузере.</b>")
    else:
        await state.update_data(debug_menu=False)

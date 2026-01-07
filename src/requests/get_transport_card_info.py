import logging
import os
import re
from datetime import timedelta, datetime

import requests
from babel.dates import format_datetime

from src.models.mosmetro.lk_response_troika import LKTroika, Card
from src.models.mosmetro.search_response_troika import Troika
from src.utils.load_config import load_config

config = load_config()

kind_emojis = {
    "electrobus": "⚡",
    "bus": "🚌",
    "tram": "🚊",
    "trolleybus": "🚎"
}


def get_troika_info(card_number: str) -> str | None:
    response = requests.get(f"{os.getenv("BACKEND_URL")}{os.getenv("PORT")}/mosmetro/troika/card_number/{card_number}")
    msg = ""

    if not response.ok:
        logging.warning(f"API request error: {response.text}")
        return None

    troika_data = Troika(**response.json())
    troika = troika_data.card
    products = troika_data.availableProducts

    troika_info = (
        f"💳 <b>Карта «Тройка» | {troika.cardNumber}</b>\n"
        f"<i>{'Лимитированная транспортная карта «' + re.sub(r'[^0-9а-яА-Я\-]', '', troika.limited) + '»' if troika.limited else 'Обычная транспортная карта'}</i>\n"
    )

    products_info = ""
    for product in products:
        products_info += f"<i>{re.sub(r'\s{2,}', ' ', product.name.strip())}</i> | <b>{product.descr}</b> | <i>{product.price} рублей</i>\n"
        msg = '<b>ℹ Информация об транспортной карте «Тройка» и доступных для данной транспортной карты тарифах</b>\n' \
              + '\n' + troika_info + '\n' + products_info
    if not troika_info:
        return None, None
    return msg, troika.img


def get_lk_troika_info(linked_card, access_token) -> str | None:
    response = requests.get(f"{os.getenv("BACKEND_URL")}{os.getenv("PORT")}/mosmetro/troika/transport_card/?access_token={access_token}&linked_card_id={linked_card}")
    msg = ""
    info_parts = []

    if not response.ok:
        logging.warning(f"API request error: {response.text}")
        return None

    lk_troika_data = Card(**response.json())
    operations = lk_troika_data.operations
    trips = lk_troika_data.trips

    if lk_troika_data.tickets:
        end_ticket_data = datetime.today() + timedelta(days=lk_troika_data.tickets[0].remainDayCount - 1)
        status_ticket = "Активный" if lk_troika_data.tickets[0].isActive else "Неактивный"
        tickets_card = (f'{re.sub(r'\s{2,}', ' ', lk_troika_data.tickets[0].ticketName.strip())} |'
                        f' {status_ticket} |'
                        f' {lk_troika_data.tickets[0].remainDayCount} дней ({format_datetime(end_ticket_data, "'до' d MMMM YYYY 'г.'", locale='ru')})')
    else:
        tickets_card = 'Отсутствует'

    if lk_troika_data.unbalance:
        balanced_card = (f'Текущий баланс: {lk_troika_data.balance} рублей\n'
                         f'Незаписанный баланс: {lk_troika_data.unbalance} рублей')
    else:
        balanced_card = f'Текущий баланс: {lk_troika_data.balance} рублей'

    if lk_troika_data.status == "action":
        status_card = 'Активная (✅️)'
    elif lk_troika_data.status == "blocked":
        status_card = 'Заблокирована (🚫)'
    elif lk_troika_data.status == "transfer":
        status_card = 'Готова к переносу (↪)'
    elif lk_troika_data.status == "annulled":
        status_card = 'Аннулирована (🛑)'
        balanced_card = 'Текущий баланс: 0 рублей'

    if lk_troika_data.cardType == 'virtual':
        display_troika = f'💠 <b>{lk_troika_data.displayName} | {lk_troika_data.cardNumber}</b>'
    elif lk_troika_data.cardType == 'troika':
        display_troika = f'💳 <b>Карта «{lk_troika_data.cardTypeName}» | {lk_troika_data.cardNumber} | «{lk_troika_data.displayName}»</b>'
    elif lk_troika_data.cardType == 'social':
        display_troika = f'💳 <b>{lk_troika_data.cardTypeName} | {lk_troika_data.cardNumber} | «{lk_troika_data.displayName}»</b>'


    troika_info = (
        f"<b>{display_troika}</b>\n"
         f"<i>{'Лимитированная транспортная карта «' + re.sub(r'[^0-9а-яА-Я\-]', '', lk_troika_data.limitedEditionName) + '»' if lk_troika_data.limited else 'Обычная транспортная карта'}</i>\n"
        f"<i>{balanced_card}</i>\n"
        f"<i>Тариф: {tickets_card}</i>\n"
        f"<b>Статус: {status_card}</b>\n"
    )

    trips_info = ""
    for i, trip in enumerate(trips[:3], start=1):
        dt = datetime.fromtimestamp(trip.date / 1000)
        formatted_date = format_datetime(dt, "d MMMM 'в' HH:mm", locale='ru')

        if trip.tripType in ('metro', 'mcd'):
            if trip.sum == 0 or trip.sum is None:
                tripsName = (
                    f'{trip.tripName} ({trip.lineName}) | '
                    f'Бесплатный проезд по тарифу «{re.sub(r"\s{2,}", " ", trip.productTypeName.strip())}» '
                    f'({formatted_date}) | '
                    f'{config.line_emojis.get(f"{trip.lineName} линия", config.line_emojis.get(trip.lineName, "🚆"))}'
                )
            else:
                tripsName = (
                    f'{trip.tripName} ({trip.lineName}) | '
                    f'{trip.sum} рублей ({formatted_date}) | '
                    f'{config.line_emojis.get(f"{trip.lineName} линия", config.line_emojis.get(trip.lineName, "🚆"))}'
                )
        elif trip.tripType == 'ground':
            if trip.sum == 0 or trip.sum is None:
                tripsName = (
                    f'{trip.tripName} | '
                    f'Бесплатный проезд по тарифу «{re.sub(r"\s{2,}", " ", trip.productTypeName.strip())}» '
                    f'({formatted_date}) | '
                    f'{kind_emojis.get(trip.kind, "🚆")}'
                )
            else:
                tripsName = (
                    f'{trip.tripName} | '
                    f'{trip.sum} рублей ({formatted_date}) | '
                    f'{kind_emojis.get(trip.kind, "🚆")}'
                )

        trips_info += f"{['1️⃣', '2️⃣', '3️⃣'][i - 1]} <i> | {tripsName}</i>\n"

    operations_info = ""
    for i, operation in enumerate(operations[:3], start=1):
        if operation:
            dt = datetime.fromtimestamp(operation.date / 1000)
            formatted_date = format_datetime(dt, "d MMMM 'в' HH:mm", locale='ru')

            if operation.operationType == 'payment':
                if operation.payment.product.wallet:
                    operationsName = (f'Пополнение баланса |'
                                      f' {operation.payment.sum} рублей'
                                      f' ({formatted_date})')
                else:
                    operationsName = (f'Покупка тарифа |'
                                      f' «{re.sub(r"\s{2,}", " ", operation.payment.product.productName.strip())}»'
                                      f' ({formatted_date})')
            elif operation.operationType == 'deferred':
                if operation.payment.product.wallet:
                    operationsName = (f'Удаленное пополнение баланса |'
                                      f' {operation.payment.sum} рублей'
                                      f' ({formatted_date})')
                else:
                    operationsName = (f'Удаленная покупка тарифа |'
                                      f' «{re.sub(r"\s{2,}", " ", operation.payment.product.productName.strip())}»'
                                      f' ({formatted_date})')
            elif operation.operationType == 'deferredWrite':
                if operation.deferredWrite.product.wallet:
                    operationsName = (f'Запись пополнения баланса |'
                                      f' {operation.deferredWrite.sum:.0f} рублей'
                                      f' ({formatted_date})')
                else:
                    operationsName = (f'Запись тарифа |'
                                      f' «{re.sub(r"\s{2,}", " ", operation.deferredWrite.product.productName.strip())}»'
                                      f' ({formatted_date})')
            elif operation.operationType == 'transfer':
                if operation.transfer.destinationCard:
                    operationsName = (f'Перенос баланса |'
                                      f' «{operation.transfer.destinationCard.displayName}»'
                                      f' ({formatted_date})')
                else:
                    operationsName = (f'Получения переноса баланса |'
                                      f' «{operation.transfer.sourceCard.displayName}»'
                                      f' ({formatted_date})')
            elif operation.operationType == 'vtPayment':
                if operation.vtPayment.purchases[0].product.wallet:
                    operationsName = (f'Пополнение баланса |'
                                      f' {operation.vtPayment.purchases[0].amount} рублей'
                                      f' ({formatted_date})')
                else:
                    operationsName = (f'Покупка тарифа |'
                                      f' «{re.sub(r"\s{2,}", " ", operation.vtPayment.purchases[0].product.productName.strip())}»'
                                      f' ({formatted_date})')

            operations_info += f"{['1️⃣', '2️⃣', '3️⃣'][i - 1]} <i> | {operationsName}</i>\n"

    if troika_info:
        info_parts.append(troika_info)
    if trips_info:
        info_parts.append('<b>Последние поездки:</b>\n' + trips_info)
    if operations_info:
        info_parts.append('<b>Последние операции:</b>\n' + operations_info)

    if info_parts:
        msg = (
                'ℹ <b>Информация об транспортной карте из личного кабинета и доступных для данной транспортной карты взаимодействие</b>\n\n'
                + '\n'.join(info_parts)
        )

    if not troika_info:
        return None, None
    return msg, lk_troika_data.img


def get_transport_card_info(access_token: str) -> str | None:
    response = requests.get(
        f"{os.getenv("BACKEND_URL")}{os.getenv("PORT")}/mosmetro/troika/transport_card/?access_token={access_token}")
    troika_info = []
    troikaWaiting_info = []
    info_parts = []
    msg = ""

    if not response.ok:
        logging.warning(f"API request error: {response.text}")
        return None

    lk_troika_data = LKTroika(**response.json())
    troika = lk_troika_data.cards
    troikaWaiting = lk_troika_data.waitingLinkCards

    for card in troika:
        operationsName = 'Отсутствует'
        tripsName = 'Отсутствует'

        if card.cardType == "troika":
            title_card = (f"💳 Карта «{card.cardTypeName}» |"
                          f" {card.cardNumber} |"
                          f" «{card.displayName}»")
        elif card.cardType == "social":
            title_card = (f"💳 «{card.cardTypeName}» |"
                          f" {card.cardNumber} |"
                          f" «{card.displayName}»")
        elif card.cardType == "virtual":
            title_card = (f"💠 {card.cardTypeName} |"
                          f" {card.cardNumber}")

        if card.unbalance:
            balanced_card = (f'Текущий баланс: {card.balance} рублей\n'
                             f'Незаписанный баланс: {card.unbalance} рублей')
        else:
            balanced_card = f'Текущий баланс: {card.balance} рублей'

        if card.tickets:
            end_ticket_data = datetime.today() + timedelta(days=card.tickets[0].remainDayCount - 1)
            status_ticket = "Активный" if card.tickets[0].isActive else "Неактивный"
            tickets_card = (f'{re.sub(r'\s{2,}', ' ', card.tickets[0].ticketName.strip())} |'
                            f' {status_ticket} |'
                            f' {card.tickets[0].remainDayCount} дней ({format_datetime(end_ticket_data, "'до' d MMMM YYYY 'г.'", locale='ru')})')
        else:
            tickets_card = 'Отсутствует'

        if card.status == "action":
            status_card = 'Активная (✅️)'
        elif card.status == "blocked":
            status_card = 'Заблокирована (🚫)'
        elif card.status == "transfer":
            status_card = 'Готова к переносу (↪)'
        elif card.status == "annulled":
            status_card = 'Аннулирована (🛑)'
            balanced_card = 'Текущий баланс: 0 рублей'

        if card.trips:
            dt = datetime.fromtimestamp(card.trips[0].date / 1000)
            formatted_date = format_datetime(dt, "d MMMM 'в' HH:mm", locale='ru')

            if card.trips[0].tripType == 'metro' or card.trips[0].tripType == 'mcd':
                if card.trips[0].sum == 0 or card.trips[0].sum is None:
                    tripsName = (f'{card.trips[0].tripName} ({card.trips[0].lineName}) |'
                                 f' Бесплатный проезд по тарифу «{re.sub(r'\s{2,}', ' ', card.trips[0].productTypeName.strip())}» ({formatted_date}) |'
                                 f' {config.line_emojis.get(f"{card.trips[0].lineName} линия", config.line_emojis.get(card.trips[0].lineName, "🚆"))}')
                else:
                    tripsName = (f'{card.trips[0].tripName} ({card.trips[0].lineName}) |'
                                 f' {card.trips[0].sum} рублей ({formatted_date}) |'
                                 f' {config.line_emojis.get(f"{card.trips[0].lineName} линия", config.line_emojis.get(card.trips[0].lineName, "🚆"))}')
            elif card.trips[0].tripType == 'ground':
                if card.trips[0].sum == 0 or card.trips[0].sum is None:
                    tripsName = (f'{card.trips[0].tripName} |'
                                 f' Бесплатный проезд по тарифу «{re.sub(r'\s{2,}', ' ', card.trips[0].productTypeName.strip())}» ({formatted_date}) |'
                                 f' {kind_emojis.get(card.trips[0].kind, "🚆")}')
                else:
                    tripsName = (f'{card.trips[0].tripName} |'
                                 f' {card.trips[0].sum} рублей ({formatted_date}) |'
                                 f' {kind_emojis.get(card.trips[0].kind, "🚆")}')

        if card.operations:
            dt = datetime.fromtimestamp(card.operations[0].date / 1000)
            formatted_date = format_datetime(dt, "d MMMM 'в' HH:mm", locale='ru')

            if card.operations[0].operationType == 'payment':
                if card.operations[0].payment.product.wallet:
                    operationsName = (f'Пополнение баланса |'
                                      f' {card.operations[0].payment.sum} рублей'
                                      f' ({formatted_date})')
                else:
                    operationsName = (f'Покупка тарифа |'
                                      f' «{re.sub(r'\s{2,}', ' ', card.operations[0].payment.product.productName.strip())}»'
                                      f' ({formatted_date})')
            elif card.operations[0].operationType == 'deferred':
                if card.operations[0].payment.product.wallet:
                    operationsName = (f'Удаленное пополнение баланса |'
                                      f' {card.operations[0].payment.sum} рублей'
                                      f' ({formatted_date})')
                else:
                    operationsName = (f'Удаленная покупка тарифа |'
                                      f' «{re.sub(r'\s{2,}', ' ', card.operations[0].payment.product.productName.strip())}» '
                                      f' ({formatted_date})')
            elif card.operations[0].operationType == 'deferredWrite':
                if card.operations[0].deferredWrite.product.wallet:
                    operationsName = (f'Запись пополнения баланса |'
                                      f' {card.operations[0].deferredWrite.sum:.0f} рублей'
                                      f' ({formatted_date})')
                else:
                    operationsName = (f'Запись тарифа |'
                                      f' «{re.sub(r'\s{2,}', ' ', card.operations[0].deferredWrite.product.productName.strip())}»'
                                      f' на транспортную карту ({formatted_date})')
            elif card.operations[0].operationType == 'transfer':
                if card.operations[0].transfer.destinationCard:
                    operationsName = (f'Перенос баланса |'
                                      f' «{card.operations[0].transfer.destinationCard.displayName}» с номером {card.operations[0].transfer.destinationCard.cardNumber}'
                                      f' ({formatted_date})')
                else:
                    operationsName = (f'Получения переноса баланса |'
                                      f' «{card.operations[0].transfer.sourceCard.displayName}»'
                                      f' ({formatted_date})')
            elif card.operations[0].operationType == 'vtPayment':
                if card.operations[0].vtPayment.purchases[0].product.wallet:
                    operationsName = (f'Пополнение баланса |'
                                      f' {card.operations[0].vtPayment.purchases[0].amount} рублей'
                                      f' ({formatted_date})')
                else:
                    operationsName = (f'Покупка тарифа |'
                                      f' «{re.sub(r'\s{2,}', ' ', card.operations[0].vtPayment.purchases[0].product.productName.strip())}»'
                                      f' ({formatted_date})')

        this_transport_card_info = f'<b>{title_card}</b>\n' \
                                   f'<i>{balanced_card}</i>\n' \
                                   f'<i>Тариф: {tickets_card}\n</i>' \
                                   f'<i>Последняя операция: {operationsName}\n</i>' \
                                   f'<i>Последняя поездка: {tripsName}\n</i>' \
                                   f'<b>Статус: {status_card}</b>\n'

        troika_info.append(this_transport_card_info)

    for waitingCards in troikaWaiting:
        dt = datetime.fromtimestamp(waitingCards.linkByPaymentState.confirmDateTimeToUtc / 1000)
        formatted_date = format_datetime(dt, "'до' d MMMM HH:mm", locale='ru')

        now_time = datetime.now().timestamp()
        time_until_arrival = waitingCards.linkByPaymentState.confirmDateTimeToUtc / 1000 - now_time

        if time_until_arrival <= 0:
            time_until_str = 'Время для привязки транспортной карты завершено'
        else:
            total_seconds = int(time_until_arrival)
            hours, remainder = divmod(total_seconds, 3600)
            minutes, _ = divmod(remainder, 60)

            if hours == 0:
                time_until_str = f'Привязка активна в течении: {minutes} мин. ({formatted_date})'
            else:
                time_until_str = f'Привязка активна в течении: {hours} час {minutes} мин. ({formatted_date})'

        if waitingCards.linkByPaymentState.status == "waitingPayment":
            waitingCards_description = f'Необходимо пополнить баланс на {waitingCards.linkByPaymentState.confirmSum} рублей для привязки к личному кабинету'
            status_card_waiting = 'Ожидает пополнения (⚠️)'
        elif waitingCards.linkByPaymentState.status == "waitingCard":
            waitingCards_description = f'Запишите пополнение {waitingCards.linkByPaymentState.confirmSum} рублей удобным для вас способом до окончания времени привязки'
            status_card_waiting = 'Ожидает запись пополнения (💳⚠️)'

        this_waiting_transport_card_info = f'💳 <b>Карта «{waitingCards.cardTypeName}» | {waitingCards.cardNumber} | «{waitingCards.displayName}»</b>\n' \
                                           f'<i>{waitingCards_description}\n</i>' \
                                           f'<i>{time_until_str}\n</i>' \
                                           f'<b>Статус: {status_card_waiting}</b>\n'

        troikaWaiting_info.append(this_waiting_transport_card_info)

    if troika_info:
        info_parts.extend(troika_info)
    if troikaWaiting_info:
        info_parts.extend(troikaWaiting_info)

    if info_parts:
        msg = (
                'ℹ <b>Информация об привязанных транспортных картах в личном кабинете</b>\n\n'
                + '\n'.join(info_parts)
        )

    return msg if troika_info or troikaWaiting_info else None

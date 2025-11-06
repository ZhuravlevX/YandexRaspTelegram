import logging
import os
import re
from datetime import timedelta, datetime

import requests
from babel.dates import format_datetime

from src.models.mosmetro.lk_response_troika import LKTroika
from src.models.mosmetro.operations_card import Operations
from src.models.mosmetro.search_response_troika import Troika
from src.models.mosmetro.trips_card import Trips
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
        f"💳 <b>Карта «Тройка» | Номер карты: {troika.cardNumber}</b>\n"
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

        # headers = {
        #     "User-Agent": "MosMetro/4.2.3 (7874) (Android; samsung SM-A155F; 15; 2629830780)",
        #     "Authorization": f"Bearer {access_token}"
        # }
        # trips_url = f"{os.getenv("LK_MOSMETRO_API_URL")}/trips/v1.0?size=1&pageToken=&linkedCardIds={card.linkedCardId}"
        # trips_response = requests.get(trips_url, headers=headers)
        # lk_troika_trips = Trips(**trips_response.json())
        # trips = lk_troika_trips.data.items
        #
        # operations_payload = {
        #     "linkedCardIds": [card.linkedCardId],
        #     "operationTypes": []
        # }
        #
        # operations_url = f"{os.getenv("LK_MOSMETRO_API_URL")}/operations/v1.0?size=1&pageToken="
        # operations_response = requests.post(operations_url, json=operations_payload, headers=headers)
        # lk_troika_operations = Operations(**operations_response.json())
        # operations = lk_troika_operations.data.items

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
                                 f' {config.line_emojis.get(f"{card.trips[0].lineName} линия", config.line_emojis.get(card.trips[0].lineName, "🚈"))}')
                else:
                    tripsName = (f'{card.trips[0].tripName} ({card.trips[0].lineName}) |'
                                 f' {card.trips[0].sum} рублей ({formatted_date}) |'
                                 f' {config.line_emojis.get(f"{card.trips[0].lineName} линия", config.line_emojis.get(card.trips[0].lineName, "🚈"))}')
            elif card.trips[0].tripType == 'ground':
                if card.trips[0].sum == 0 or card.trips[0].sum is None:
                    tripsName = (f'{card.trips[0].tripName} |'
                                 f' Бесплатный проезд по тарифу «{re.sub(r'\s{2,}', ' ', card.trips[0].productTypeName.strip())}» ({formatted_date}) |'
                                 f' {kind_emojis.get(card.trips[0].kind, "🚈")}')
                else:
                    tripsName = (f'{card.trips[0].tripName} |'
                                 f' {card.trips[0].sum} рублей ({formatted_date}) |'
                                 f' {kind_emojis.get(card.trips[0].kind, "🚈")}')

        if card.operations:
            dt = datetime.fromtimestamp(card.operations[0].date / 1000)
            formatted_date = format_datetime(dt, "d MMMM 'в' HH:mm", locale='ru')

            if card.operations[0].operationType == 'payment':
                if card.operations[0].payment.product.wallet:
                    operationsName = (f'Пополнение на'
                                      f' {card.operations[0].payment.sum} рублей'
                                      f' ({formatted_date})')
                else:
                    operationsName = (f'Покупка тарифа'
                                      f' «{re.sub(r'\s{2,}', ' ', card.operations[0].payment.product.productName.strip())}»'
                                      f' ({formatted_date})')
            elif card.operations[0].operationType == 'deferred':
                if card.operations[0].payment.product.wallet:
                    operationsName = (f'Удаленное пополнение на'
                                      f' {card.operations[0].payment.sum} рублей'
                                      f' ({formatted_date})')
                else:
                    operationsName = (f'Удаленная покупка тарифа '
                                      f'«{re.sub(r'\s{2,}', ' ', card.operations[0].payment.product.productName.strip())}» '
                                      f'({formatted_date})')
            elif card.operations[0].operationType == 'deferredWrite':
                if card.operations[0].deferredWrite.product.wallet:
                    operationsName = (f'Запись пополнения баланса на'
                                      f' {card.operations[0].deferredWrite.sum:.0f} рублей'
                                      f' ({formatted_date})')
                else:
                    operationsName = (f'Запись тарифа'
                                      f' «{re.sub(r'\s{2,}', ' ', card.operations[0].deferredWrite.product.productName.strip())}»'
                                      f' на транспортную карту ({formatted_date})')
            elif card.operations[0].operationType == 'transfer':
                if card.operations[0].transfer.destinationCard:
                    operationsName = (f'Перенос баланса на транспортную карту'
                                      f' «{card.operations[0].transfer.destinationCard.displayName}» с номером {card.operations[0].transfer.destinationCard.cardNumber}'
                                      f' ({formatted_date})')
                else:
                    operationsName = (f'Перенос баланса c транспортной карты'
                                      f' «{card.operations[0].transfer.sourceCard.displayName}» с номером {card.operations[0].transfer.sourceCard.cardNumber}'
                                      f' ({formatted_date})')
            elif card.operations[0].operationType == 'vtPayment':
                if card.operations[0].vtPayment.purchases[0].product.wallet:
                    operationsName = (f'Пополнение на'
                                      f' {card.operations[0].vtPayment.purchases[0].amount} рублей'
                                      f' ({formatted_date})')
                else:
                    operationsName = (f'Покупка тарифа'
                                      f' «{re.sub(r'\s{2,}', ' ', card.operations[0].vtPayment.purchases[0].product.productName.strip())}»'
                                      f' ({formatted_date})')


        # if operations:
        #     dt = datetime.fromtimestamp(operations[0].date / 1000)
        #     formatted_date = format_datetime(dt, "d MMMM 'в' HH:mm", locale='ru')
        #
        #     if operations[0].type == 'payment':
        #         if operations[0].payment.product.wallet:
        #             operationsName = f'Пополнение на {operations[0].payment.sum:.0f} рублей ({formatted_date})'
        #         else:
        #             operationsName = f'Покупка тарифа «{re.sub(r'\s{2,}', ' ', operations[0].payment.product.productName.strip())}» ({formatted_date})'
        #     elif operations[0].type == 'deferred':
        #         if operations[0].payment.product.wallet:
        #             operationsName = f'Удаленное пополнение на {operations[0].payment.sum:.0f} рублей ({formatted_date})'
        #         else:
        #             operationsName = f'Удаленная покупка тарифа «{re.sub(r'\s{2,}', ' ', operations[0].payment.product.productName.strip())}» ({formatted_date})'
        #     elif operations[0].type == 'deferredWrite':
        #         if operations[0].deferredWrite.product.wallet:
        #             operationsName = f'Запись пополнения баланса на {operations[0].deferredWrite.sum:.0f} рублей ({formatted_date})'
        #         else:
        #             operationsName = f'Запись тарифа «{re.sub(r'\s{2,}', ' ', operations[0].deferredWrite.product.productName.strip())}» на транспортную карту ({formatted_date})'
        #     elif operations[0].type == 'transfer':
        #         if operations[0].transfer.destinationCard:
        #             operationsName = f'Перенос баланса на транспортную карту «{operations[0].transfer.destinationCard.displayName}» с номером {operations[0].transfer.destinationCard.cardNumber} ({formatted_date})'
        #         else:
        #             operationsName = f'Перенос баланса c транспортной карты «{operations[0].transfer.sourceCard.displayName}» с номером {operations[0].transfer.sourceCard.cardNumber} ({formatted_date})'
        #
        # if trips:
        #     dt = datetime.fromtimestamp(trips[0].trip.date / 1000)
        #     formatted_date = format_datetime(dt, "d MMMM 'в' HH:mm", locale='ru')
        #
        #     if trips[0].trip.type == 'metro' or trips[0].trip.type == 'mcd':
        #         if trips[0].operation.sum == 0 or trips[0].operation.sum is None:
        #             tripsName = f'{trips[0].displayName} ({trips[0].trip.metroDetails.lines[0].name}) | Бесплатный проезд по тарифу «{re.sub(r'\s{2,}', ' ', trips[0].operation.typeName.strip())}» ({formatted_date}) | {config.line_emojis.get(f"{trips[0].trip.metroDetails.lines[0].name} линия", config.line_emojis.get(trips[0].trip.metroDetails.lines[0].name, "🚈"))}'
        #         else:
        #             tripsName = f'{trips[0].displayName} ({trips[0].trip.metroDetails.lines[0].name}) | {trips[0].operation.sum:.0f} рублей ({formatted_date}) | {config.line_emojis.get(f"{trips[0].trip.metroDetails.lines[0].name} линия", config.line_emojis.get(trips[0].trip.metroDetails.lines[0].name, "🚈"))}'
        #     elif trips[0].trip.type == 'ground':
        #         if trips[0].operation.sum == 0 or trips[0].operation.sum is None:
        #             tripsName = f'{trips[0].displayName} | Бесплатный проезд по тарифу «{re.sub(r'\s{2,}', ' ', trips[0].operation.typeName.strip())}» ({formatted_date}) | {kind_emojis.get(trips[0].trip.groundDetails.kind, "🚈")}'
        #         else:
        #             tripsName = f'{trips[0].displayName} | {trips[0].operation.sum:.0f} рублей ({formatted_date}) | {kind_emojis.get(trips[0].trip.groundDetails.kind, "🚈")}'

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

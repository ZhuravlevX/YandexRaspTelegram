import logging
import os

import requests
from src.models.mosmetro.search_response_troika import Troika
from src.utils.load_config import load_config

config = load_config()


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
        f"💳 <b>{troika.displayName} | Номер карты: {troika.cardNumber}</b>\n"
        f"<i>{'Лимитированная транспортная карта «' + troika.limited + '»' if troika.limited else 'Обычная транспортная карта'}</i>\n"
    )

    products_info = ""
    for product in products:
        products_info += f"<i>{product.name}</i> | <b>{product.descr}</b> | <i>{product.price} рублей</i>\n"
        msg = '<b>ℹ Информация об транспортной карте «Тройка» и доступных для данной транспортной карты тарифах</b>\n' \
              + '\n' + troika_info + '\n' + products_info
    return msg if troika_info else None

def get_troika_image(card_number: str) -> str | None:
    response = requests.get(f"{os.getenv("BACKEND_URL")}{os.getenv("PORT")}/mosmetro/troika/card_number/{card_number}")
    if not response.ok:
        logging.warning(f"API request error: {response.text}")
        return None

    troika_data = Troika(**response.json())
    troika = troika_data.card
    return troika.img

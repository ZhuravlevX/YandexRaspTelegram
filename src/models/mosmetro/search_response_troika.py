from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel


class Card(BaseModel):
    uid: str
    cardNumber: str
    displayName: str
    limited: Optional[str]
    cardType: str
    img: str


class AvailableProduct(BaseModel):
    id: int
    name: str
    descr: str
    price: int


class Troika(BaseModel):
    card: Card
    availableProducts: List[AvailableProduct]

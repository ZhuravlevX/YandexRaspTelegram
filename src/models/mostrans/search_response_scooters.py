from __future__ import annotations
from typing import List
from pydantic import BaseModel


class Scooters(BaseModel):
    scooters: List[Scooter]


class Charge(BaseModel):
    percent: int


class Organisation(BaseModel):
    id: str
    name: str


class Scooter(BaseModel):
    name: str
    id: str
    code: str
    charge: Charge
    lat: float
    lng: float
    remainKm: int
    minutePrice: str
    price: str
    organisation: Organisation

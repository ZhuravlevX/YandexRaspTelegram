from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel


class Trips(BaseModel):
    data: Optional[Data]
    success: Optional[bool]


class GroundDetails(BaseModel):
    id: str
    routeId: str
    kind: str
    icon: str


class Line(BaseModel):
    id: str
    icon: str
    name: str


class MetroDetails(BaseModel):
    id: str
    lines: List[Line]


class Trip(BaseModel):
    date: int
    type: str
    groundDetails: Optional[GroundDetails] = None
    metroDetails: Optional[MetroDetails] = None
    transfer: Optional[Transfer] = None
    isFacePay: bool

class Transfer(BaseModel):
    kind: str

class Operation(BaseModel):
    id: str
    sum: float
    tripCount: int
    type: str
    typeId: str
    typeName: str
    icon: str


class Card(BaseModel):
    cardNumber: str
    socialCardNumber: Optional[str] = None
    displayName: str
    limited: bool
    cardType: str
    cardTypeName: str
    icon: str
    img: str
    linkedCardId: str


class Item(BaseModel):
    id: str
    displayName: str
    trip: Trip
    operation: Operation
    paymentType: str
    card: Card


class Data(BaseModel):
    items: Optional[List[Item]]
    nextPageToken: Optional[str] = None

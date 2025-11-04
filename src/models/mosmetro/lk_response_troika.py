from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel


class LKTroika(BaseModel):
    cards: List[Card]
    waitingLinkCards: List[WaitingLinkCard]


class Ticket(BaseModel):
    ticketName: str
    remainDayCount: int
    productId: str
    isActive: bool
    totalDaysCount: int


class LinkByPaymentState(BaseModel):
    confirmDateTimeToUtc: int
    confirmSum: int
    status: str


class WaitingLinkCard(BaseModel):
    cardNumber: str
    linkedCardId: str
    cardUid: str
    cardType: str
    cardTypeName: str
    displayName: str
    linkByPaymentState: LinkByPaymentState


class DestinationCard(BaseModel):
    cardNumber: str
    displayName: str
    limited: bool
    cardType: str


class Payment(BaseModel):
    income: bool
    sum: float
    sourceType: str
    sourcePaymentType: str
    receiptUrl: Optional[str] = None
    product: Product


class Transfer(BaseModel):
    product: Product
    balance: int
    destinationCard: DestinationCard


class Product(BaseModel):
    productId: str
    productType: Optional[str] = None
    productName: str
    icon: Optional[str] = None
    img: Optional[str] = None
    wallet: Optional[bool] = None
    vtbProductId: Optional[str] = None

class Operation(BaseModel):
    operationName: str
    date: int
    operationType: str
    payment: Optional[Payment]
    deferredWrite: Optional[DeferredWrite]
    transfer: Optional[Transfer]


class DeferredWrite(BaseModel):
    sum: int
    cardBalance: int
    product: Product
    deviceTypeName: str
    deviceTypeId: str


class Card(BaseModel):
    cardNumber: str
    linkedCardId: str
    cardTypeName: str
    displayName: str
    cardType: str
    status: str
    balance: int
    unbalance: Optional[int]
    untickets: List
    tickets: List[Ticket]
    operations: List[Operation]
    trips: List[Trip]


class Trip(BaseModel):
    tripName: str
    tripType: str
    productTypeName: str
    date: int
    isFacePay: bool
    sum: int
    kind: Optional[str]
    lineName: Optional[str]

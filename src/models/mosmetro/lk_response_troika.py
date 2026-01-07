from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel


class LKTroika(BaseModel):
    cards: Optional[List[Card]]
    waitingLinkCards: Optional[List[WaitingLinkCard]]


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
    cardType: str


class SourceCard(BaseModel):
    cardNumber: str
    displayName: str
    cardType: str


class Payment(BaseModel):
    sum: int
    receiptUrl: Optional[str] = None
    product: Product


class Transfer(BaseModel):
    product: Product
    destinationCard: Optional[DestinationCard]
    sourceCard: Optional[SourceCard]


class Product(BaseModel):
    productId: str
    productName: str
    wallet: bool


class Operation(BaseModel):
    operationName: str
    date: int
    operationType: str
    payment: Optional[Payment]
    deferredWrite: Optional[DeferredWrite]
    transfer: Optional[Transfer]
    vtPayment: Optional[VtPayment]


class Purchase(BaseModel):
    amount: int
    product: Product
    receiptUrl: Optional[str] = None


class VtPayment(BaseModel):
    purchases: List[Purchase]


class DeferredWrite(BaseModel):
    sum: int
    product: Product


class AvailableProducts(BaseModel):
    id: str
    name: str
    descr: Optional[str]
    price: int


class Card(BaseModel):
    cardNumber: str
    linkedCardId: str
    cardTypeName: str
    displayName: str
    cardType: str
    status: str
    img: Optional[str] = None
    limited: Optional[bool] = None
    limitedEditionName: Optional[str] = None
    balance: int
    unbalance: Optional[int]
    untickets: List
    tickets: List[Ticket]
    operations: List[Operation]
    trips: List[Trip]
    availableProducts: Optional[List[AvailableProducts]]


class Trip(BaseModel):
    tripName: str
    tripType: str
    productTypeName: str
    date: int
    isFacePay: bool
    sum: int
    kind: Optional[str]
    lineName: Optional[str]

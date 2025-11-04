from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel


class Operations(BaseModel):
    data: Optional[Data]
    success: Optional[bool]


class Card(BaseModel):
    cardNumber: str
    socialCardNumber: Optional[str] = None
    displayName: str
    limited: bool
    limitedEditionName: Optional[str] = None
    cardType: str
    cardTypeName: str
    icon: str
    img: str
    linkedCardId: str


class Product(BaseModel):
    productId: str
    productType: str
    productName: str
    icon: str
    img: str
    wallet: bool
    vtbProductId: str


class Payment(BaseModel):
    income: bool
    sum: float
    sourceType: str
    sourcePaymentType: str
    receiptUrl: Optional[str] = None
    product: Product

class Transfer(BaseModel):
    product: Product
    balance: float
    destinationCard: Optional[DestinationCard] = None
    sourceCard: Optional[SourceCard] = None

class SourceCard(BaseModel):
    cardNumber: str
    displayName: str
    limited: bool
    cardType: str

class DestinationCard(BaseModel):
    cardNumber: str
    displayName: str
    limited: bool
    cardType: str

class DeferredWrite(BaseModel):
    sum: float
    cardBalance: float
    product: Product
    deviceTypeName: str
    deviceTypeId: str

class Item(BaseModel):
    id: str
    displayName: str
    type: str
    status: str
    card: Optional[Card] = None
    date: int
    payment: Optional[Payment] = None
    deferredWrite: Optional[DeferredWrite] = None
    transfer: Optional[Transfer] = None


class Data(BaseModel):
    items: List[Item]
    nextPageToken: Optional[str] = None

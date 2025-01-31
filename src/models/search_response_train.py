from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class SearchResponse(BaseModel):
    search: Search
    segments: List[Segment]
    interval_segments: List
    pagination: Pagination


class Segment(BaseModel):
    thread: Thread
    stops: str
    from_: From = Field(..., alias='from')
    to: To
    departure_platform: str
    arrival_platform: str
    departure_terminal: Any
    arrival_terminal: Any
    duration: float
    has_transfers: bool
    tickets_info: Optional[TicketsInfo]
    departure: datetime
    arrival: datetime
    start_date: datetime


class Thread(BaseModel):
    number: str
    title: str
    short_title: str
    express_type: Optional[str]
    transport_type: str
    carrier: Carrier
    uid: str
    vehicle: Any
    transport_subtype: Optional[TransportSubtype]
    thread_method_link: str


class From(BaseModel):
    type: str
    title: str
    short_title: Optional[str]
    popular_title: Optional[str]
    code: str


class To(BaseModel):
    type: str
    title: str
    short_title: Optional[str]
    popular_title: Optional[str]
    code: str


class Search(BaseModel):
    from_: From = Field(..., alias='from')
    to: To
    date: str


class Codes(BaseModel):
    sirena: Any
    iata: Any
    icao: Any


class Carrier(BaseModel):
    code: int
    title: Optional[str]
    codes: Codes
    address: Optional[str]
    url: Optional[str]
    email: Optional[str]
    contacts: Optional[str]
    phone: Optional[str]
    logo: Optional[str]
    logo_svg: Any


class TransportSubtype(BaseModel):
    title: Optional[str]
    code: Optional[str]
    color: Optional[str]

class Price(BaseModel):
    whole: int
    cents: int


class Place(BaseModel):
    name: Any
    price: Price
    currency: str


class TicketsInfo(BaseModel):
    et_marker: bool
    places: List[Place]

class Pagination(BaseModel):
    total: int
    limit: int
    offset: int

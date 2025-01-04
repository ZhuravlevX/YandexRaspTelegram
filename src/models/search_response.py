from __future__ import annotations
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
    departure: str
    arrival: str
    start_date: str


class Thread(BaseModel):
    number: str
    title: str
    short_title: str
    express_type: Optional[str]
    transport_type: str
    carrier: Carrier
    uid: str
    vehicle: Any
    transport_subtype: TransportSubtype
    thread_method_link: str


class From(BaseModel):
    type: str
    title: str
    short_title: str
    popular_title: str
    code: str
    station_type: str
    station_type_name: str
    transport_type: str


class To(BaseModel):
    type: str
    title: str
    short_title: Optional[str]
    popular_title: Optional[str]
    code: str
    station_type: str
    station_type_name: str
    transport_type: str


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
    title: str
    codes: Codes
    address: str
    url: str
    email: str
    contacts: str
    phone: str
    logo: str
    logo_svg: Any


class TransportSubtype(BaseModel):
    title: str
    code: str
    color: str

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

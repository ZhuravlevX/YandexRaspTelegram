from __future__ import annotations

from typing import Any, List, Optional
from pydantic import BaseModel

class SearchResponseStation(BaseModel):
    station: Station
    pagination: Pagination
    schedule: List[ScheduleItem]
    interval_schedule: List
    directions: List[Direction]
    schedule_direction: ScheduleDirection

class Station(BaseModel):
    type: str
    title: str
    short_title: Any
    popular_title: Any
    code: str
    station_type: str
    station_type_name: str
    transport_type: str


class Pagination(BaseModel):
    total: int
    limit: int
    offset: int


class Codes(BaseModel):
    sirena: Any
    iata: Any
    icao: Any


class Carrier(BaseModel):
    code: int
    title: str
    codes: Codes


class TransportSubtype(BaseModel):
    title: str
    code: str
    color: str


class Thread(BaseModel):
    number: str
    title: str
    short_title: str
    express_type: Any
    transport_type: str
    carrier: Carrier
    uid: str
    vehicle: Any
    transport_subtype: TransportSubtype


class ScheduleItem(BaseModel):
    thread: Thread
    is_fuzzy: bool
    platform: str
    terminal: Any
    days: str
    except_days: Optional[str]
    stops: str
    direction: str
    departure: str
    arrival: str


class Direction(BaseModel):
    code: str
    title: str


class ScheduleDirection(BaseModel):
    code: str
    title: str
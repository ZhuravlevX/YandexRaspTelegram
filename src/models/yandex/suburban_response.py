from __future__ import annotations
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class SuburbanResponse(BaseModel):
    number: str
    title: str
    short_title: str
    express_type: Any
    transport_type: str
    carrier: Carrier
    uid: str
    vehicle: Any
    transport_subtype: TransportSubtype
    days: str
    except_days: str
    stops: List[Stop]
    from_: Any = Field(..., alias='from')
    to: Any
    start_date: str
    arrival_date: Any
    departure_date: Any
    start_time: str


class Codes(BaseModel):
    sirena: Any
    iata: Any
    icao: Any


class Carrier(BaseModel):
    code: int
    title: str
    codes: Codes
    offices: List


class TransportSubtype(BaseModel):
    title: str
    code: str
    color: str


class Station(BaseModel):
    type: str
    title: str
    short_title: Optional[str]
    popular_title: Optional[str]
    code: str
    station_type: str
    station_type_name: str
    transport_type: str


class Stop(BaseModel):
    station: Station
    departure: Optional[str]
    arrival: Optional[str]
    duration: int
    stop_time: Optional[int]
    platform: str
    terminal: Any

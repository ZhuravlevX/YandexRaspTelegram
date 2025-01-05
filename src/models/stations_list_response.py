from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class StationsListResponse(BaseModel):
    countries: List[Country]

class Codes(BaseModel):
    yandex_code: Optional[str] = None


class Station(BaseModel):
    direction: str
    codes: Codes
    station_type: str
    title: str
    longitude: float | str
    transport_type: str
    latitude: float | str


class Settlement(BaseModel):
    title: str
    codes: Codes
    stations: List[Station]


class Region(BaseModel):
    settlements: List[Settlement]
    codes: Dict[str, Any]
    title: str

class Country(BaseModel):
    regions: List[Region]
    codes: Codes
    title: str


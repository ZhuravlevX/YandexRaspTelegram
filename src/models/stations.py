from typing import Optional
from pydantic import BaseModel


class Station(BaseModel):
    title: str
    code: str
    latitude: float
    longitude: float
    region: str
    station_type: str

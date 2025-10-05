from __future__ import annotations

from typing import List

from pydantic import BaseModel


class Stop(BaseModel):
    id: str
    num: int
    name: str
    lat: float
    lon: float


class RoutePath(BaseModel):
    id: str
    stops: List[Stop]
    endStopName: str
    lineColor: str
    lineTransparent: bool


class Direction(BaseModel):
    firstStopName: str
    lastStopName: str
    routePaths: List[RoutePath]


class Route(BaseModel):
    id: str
    number: str
    type: str
    directions: List[Direction]
    contractor: str
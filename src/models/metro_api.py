from typing import List

from pydantic import BaseModel


class StationMini(BaseModel):
    id: int
    name: str
    lineId: int
    lineName: str

class SearchResponse(BaseModel):
    success: bool
    count: int
    stations: List[StationMini]

class Part(BaseModel):
    nodes: List[StationMini]
    duration: int


class RouterResponse(BaseModel):
    success: bool
    parts: List[Part]
    duration: int

class Train(BaseModel):
    id: str
    way: str
    prevStation: int
    nextStation: int
    arrivalTime: int
    trainIndex: int
    wagons: dict[int, str]

class Wagons(BaseModel):
    success: bool
    data: dict[str, List[Train]]


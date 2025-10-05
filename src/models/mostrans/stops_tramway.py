from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel

class StopsTramway(BaseModel):
    id: str
    name: str
    routePath: List[RoutePathItem]

class ExternalForecastItem(BaseModel):
    time: int
    tmId: int
    routePathId: str

class RoutePathItem(BaseModel):
    id: str
    type: str
    number: str
    lastStopName: str
    externalForecast: List[ExternalForecastItem]
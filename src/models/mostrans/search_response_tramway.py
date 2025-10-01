from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel

class SearchResponse(BaseModel):
    id: str
    name: str
    type: str
    routePath: List[RoutePathItem]

class ExternalForecastItem(BaseModel):
    time: int
    byTelemetry: int
    tmId: int
    routePathId: str

class RoutePathItem(BaseModel):
    id: str
    type: str
    number: str
    lastStopName: str
    cityShuttle: bool
    sberShuttle: bool
    electrobus: bool
    rateUrl: Optional[str]
    externalForecast: List[ExternalForecastItem]
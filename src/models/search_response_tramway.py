from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel


class SearchResponse(BaseModel):
    id: str
    name: str
    type: str
    wifi: bool
    bench: Any
    elevator: Any
    comment: List
    hub: List
    photo: Any
    commentTotalCount: int
    routePath: List[RoutePathItem]
    color: str
    routeNumber: str
    isFavorite: bool
    shareUrl: str
    lat: float
    lon: float
    cityShuttle: bool
    electrobus: bool
    transportTypes: List[str]
    routeName: Any
    shuttleType: Any
    regional: bool
    testMode: bool
    debug: List


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
    color: str
    fontColor: str
    cityShuttle: bool
    sberShuttle: bool
    electrobus: bool
    rateUrl: Any
    externalForecast: List[ExternalForecastItem]
    externalForecastTime: List
    feature: Any
    isFavorite: bool
    messages: List

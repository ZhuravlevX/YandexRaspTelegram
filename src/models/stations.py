from pydantic import BaseModel


class Station(BaseModel):
    title: str
    code: str
    region: str
    station_type: str

from pydantic import BaseModel


class City(BaseModel):
    region: str
    country: str
    code: str
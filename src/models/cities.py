from pydantic import BaseModel


class City(BaseModel):
    region: str
    code: str
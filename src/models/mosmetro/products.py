from __future__ import annotations
from typing import List
from pydantic import BaseModel

class Troika(BaseModel):
    __root__: List[Product]

class Product(BaseModel):
    name: str
    descr: str
    priceMin: int

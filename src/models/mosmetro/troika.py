from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class Model(BaseModel):
    cardNumber: str
    displayName: str
    limited: Optional[str]
    cardType: str
    img: str

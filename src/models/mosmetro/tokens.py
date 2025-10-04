from __future__ import annotations
from pydantic import BaseModel


class Token(BaseModel):
    id_token: str
    access_token: str
    expires_in: int
    token_type: str
    refresh_token: str
    scope: str

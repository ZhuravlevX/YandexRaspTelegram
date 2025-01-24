from pydantic import BaseModel


class Config(BaseModel):
    suburban_urls: list[str]
    train_urls: list[str]
    emoji_map: dict[str, str]
    train_map: dict[str, str]

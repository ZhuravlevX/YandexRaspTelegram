from pydantic import BaseModel


class Config(BaseModel):
    suburban_urls: list[str]
    train_urls: list[str]
    suburban_map: dict[str, str]
    train_map: dict[str, str]
    russian_timezones: dict[str, str]

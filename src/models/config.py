from pydantic import BaseModel


class Config(BaseModel):
    suburban_urls: list[str]
    underground_urls: list[str]
    train_urls: list[str]
    suburban_map: dict[str, str]
    numbers_trains_maps_emojis: dict[str, str]
    numbers_trains_maps_title: dict[str, str]
    russian_timezones: dict[str, str]

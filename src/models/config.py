from pydantic import BaseModel


class Config(BaseModel):
    image_urls: list[str]
    emoji_map: dict[str, str]

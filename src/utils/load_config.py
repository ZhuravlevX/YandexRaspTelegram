import json5

from src.models.config import Config


def load_config() -> Config:
    with open('config.json5', 'r', encoding='utf-8') as config_file:
        config = Config(**json5.load(config_file))
    return config

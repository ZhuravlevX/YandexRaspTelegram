import json

from src.models.config import Config


def load_config() -> Config:
    with open('config.json', 'r', encoding='utf-8') as config_file:
        config = Config(**json.load(config_file))
    return config

import logging
import os

import requests
from src.models.mosmetro.tokens import Token
from src.utils.load_config import load_config

config = load_config()

def get_new_access_token(refresh_token: str):
    url = "https://auth.mosmetro.ru/connect/token"
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {os.getenv("AUTHORIZATION_BASIC")}",
        "User-Agent": "MosMetro/4.2.3 (7874) (Android; samsung SM-A155F; 15; 2629830780)"
    }

    response = requests.post(url, data=payload, headers=headers)
    profile = Token(**response.json())

    if not response.ok:
        logging.warning(f"API request error: {response.text}")
        return None
    return profile.access_token, profile.expires_in

if __name__ == "__main__":
    print(get_new_access_token())

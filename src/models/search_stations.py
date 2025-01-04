import json
import os
import re
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()
token_yandex = os.getenv('TOKEN_YANDEX')
token_bot = os.getenv('TOKEN_BOT')
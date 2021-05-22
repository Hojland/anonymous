import os
from typing import List

import pytz
from dotenv import load_dotenv
from pydantic import AnyHttpUrl, BaseSettings, HttpUrl, SecretStr
from datetime import timedelta

load_dotenv()


class Settings(BaseSettings):
    LOCAL_TZ = pytz.timezone("Europe/Copenhagen")
    ENDPOINT_PORT: int = 5000


settings = Settings()

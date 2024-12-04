# app/settings.py
from pydantic import BaseSettings
import os


class Settings(BaseSettings):
    authjwt_secret_key: str = "SECRET_KEY"
    # boshqa sozlamalarni shu yerda qo'shishingiz mumkin

class PayMeSettings:
    BASE_URL = os.getenv("DOMAIN_URL")
    MERCHANT_ID = os.getenv("MERCHANT_ID")
    SECRET_KEY = os.getenv("SECRET_KEY")
    CALLBACK_URL = os.getenv("CALLBACK_URL")
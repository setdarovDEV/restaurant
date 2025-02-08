# app/settings.py
import base64
from pydantic import BaseSettings
import os
from dotenv import load_dotenv


class Settings(BaseSettings):
    authjwt_secret_key: str = "SECRET_KEY"
    # boshqa sozlamalarni shu yerda qo'shishingiz mumkin

load_dotenv()

class PaymeConfig:
    MERCHANT_ID = os.getenv("PAYME_MERCHANT_ID")
    SECRET_KEY = os.getenv("PAYME_SECRET_KEY")
    PAYME_URL = "https://checkout.paycom.uz"  # To‘lov linki uchun
    API_URL = "https://checkout.paycom.uz/api"

def get_auth_header():
    auth_string = f"{PaymeConfig.MERCHANT_ID}:{PaymeConfig.SECRET_KEY}"
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")
    return {"Authorization": f"Basic {auth_base64}"}
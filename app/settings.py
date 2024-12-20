# app/settings.py
from pydantic import BaseSettings
import os


class Settings(BaseSettings):
    authjwt_secret_key: str = "SECRET_KEY"
    # boshqa sozlamalarni shu yerda qo'shishingiz mumkin

PAYME_ID = "675939f5e64d929b0e4760a4"
PAYME_KEY = "kXdjH?Ji#J4ts3mfmSxm&em77Z6tsc?0V%NM"
PAYME_ACCOUNT_FIELD = "order_id"
PAYME_AMOUNT_FIELD = "total_amount"
PAYME_ACCOUNT_MODEL = "app.models.Order"  # Model yo'li
PAYME_ONE_TIME_PAYMENT = True

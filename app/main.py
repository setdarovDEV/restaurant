import requests
from datetime import timedelta
from fastapi import FastAPI
from fastapi_jwt_auth import AuthJWT
from pydantic import BaseModel
from app.routers.auth import auth_router
from app.routers.orders import order_router
from app.routers.menu import menu_router
from app.routers.payment import payment_router
from app.routers.statistics import statistics_router
from app.routers.table import table_router
from app.routers.reservation import reservation_router


app = FastAPI()
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(order_router, prefix="/orders", tags=["Orders"])
app.include_router(menu_router, prefix="/menu", tags=["Menu"])
app.include_router(table_router, prefix="/table", tags=["Table"])
app.include_router(reservation_router, prefix="/reservation", tags=["Reservation"])
app.include_router(statistics_router, prefix="/statistics", tags=["Statistics"])
app.include_router(payment_router, prefix="/payment", tags=["Payment"])


class Settings(BaseModel):
    authjwt_secret_key: str = '77db53cb8e5cf81997d16101e70aec714981e3e8dee5338fe4e16b9f0a4b7821'
    authjwt_access_token_expires: timedelta = timedelta(minutes=60)
    authjwt_refresh_token_expires: timedelta = timedelta(days=7)


@AuthJWT.load_config
def get_config():
    return Settings()


@app.get("/")
async def root():
    return {"message": "Welcome to restaurant project"}


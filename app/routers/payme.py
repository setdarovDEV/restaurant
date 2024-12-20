from urllib.request import Request

from fastapi import APIRouter, HTTPException

from app.schemas import CheckPerformResponse, CheckPerformRequest
from app.services.payme import PaymeClient
import os
import httpx


payme_router = APIRouter()
payme_client = PaymeClient(
    os.getenv('PAYME_MERCHANT_ID'),
    os.getenv('PAYME_MERCHANT_KEY'),
    os.getenv('PAYME_TEST_MODE'),
)

ORDERS = {
    "1": {"status": "awaiting_payment", "amount": 10000},  # Misol uchun mavjud order
}

@payme_router.post("/check-perform", response_model=CheckPerformResponse)
async def check_perform_transaction(request: CheckPerformRequest):
    order_id = request.account.get("order_id")
    amount = request.amount

    if order_id not in ORDERS:
        raise HTTPException(status_code=400, detail="Order does not exist")

    order = ORDERS[order_id]

    if amount != order["amount"]:
        raise HTTPException(status_code=400, detail="Invalid amount")

    if order["status"] == "awaiting_payment":
        return {"allow": True, "message": "Transaction is allowed"}
    elif order["status"] == "processing":
        raise HTTPException(status_code=400, detail="Order is already being processed")
    elif order["status"] == "completed":
        raise HTTPException(status_code=400, detail="Order is already paid or cancelled")
    else:
        raise HTTPException(status_code=400, detail="Invalid order status")

@payme_router.post("/webhook")
async def webhook(data: dict):
    if data["method"] == "PerformTransaction":
        order_id = data["params"]["account"]["order_id"]
        transaction_id = data["params"]["id"]
        return {"result": {"perform_time": 123456789, "state": 1}}
    elif data["method"] == "CancelTransaction":
        return {"result": {"cancel_time": 123456789, "state": -1}}
    else:
        raise HTTPException(status_code=400, detail="Unknown method")

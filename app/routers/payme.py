from fastapi import APIRouter, HTTPException
from app.services.payme import PaymeClient
import os

payme_router = APIRouter()
payme_client = PaymeClient(
    os.getenv('PAYME_MERCHANT_ID'),
    os.getenv('PAYME_MERCHANT_KEY'),
    os.getenv('PAYME_TEST_MODE'),
)

@payme_router.post("/create-invoice/")
async def create_invoice(amount: int, order_id: str):
    try:
        response = payme_client.create_invoice(amount, order_id)
        return {
            "payment_url": f"https://checkout.test.paycom.uz/{response['result']['_id']}",
            "transaction_id": response['result']['_id']
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@payme_router.post("/check-status/")
async def check_status(transaction_id: str):
    try:
        response = payme_client.check_payment_status(transaction_id)
        return {"status": response['result']}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

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

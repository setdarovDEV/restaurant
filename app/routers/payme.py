import os
from fastapi import APIRouter, HTTPException
from app.services.payme import PaymeClient

payme_router = APIRouter()
payme_client = PaymeClient(
    os.getenv('PAYME_MERCHANT_ID'),
    os.getenv('PAYME_MERCHANT_KEY'),
    test_mode=os.getenv('PAYME_TEST_MODE') == 'True',
)

@payme_router.post("/payme/create-invoice/")
async def create_invoice(amount: int, order_id: str):
    try:
        response = payme_client.create_invoice(amount, order_id)
        return {
            "payment_url": f"https://checkout.test.paycom.uz/{response['result']['_id']}",
            "transaction_id": response['result']['_id']
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@payme_router.post("/payme/check-status/")
async def check_status(transaction_id: str):
    try:
        response = payme_client.check_payment_status(transaction_id)
        return {"status": response['result']}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@payme_router.post("/webhook")
async def webhook(data: dict):
    try:
        if data["method"] == "PerformTransaction":
            order_id = data["params"]["account"]["order_id"]
            transaction_id = data["params"]["id"]
            # Perform additional actions like updating the order status
            return {"result": {"perform_time": 123456789, "state": 1}}  # Success response
        elif data["method"] == "CancelTransaction":
            return {"result": {"cancel_time": 123456789, "state": -1}}  # Cancel response
        else:
            raise HTTPException(status_code=400, detail="Unknown method")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error in webhook: {str(e)}")

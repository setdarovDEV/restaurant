from fastapi import APIRouter, HTTPException

from app.schemas import PaymentRequest
from app.services.payme import PayMeService

payment_router = APIRouter()

@payment_router.post("/payme/create")
async def create_payment(request: PaymentRequest):
    order_id = request.order_id
    amount = request.amount
    # Logika bu yerda
    return {"order_id": order_id, "amount": amount, "status": "Payment initiated"}


@payment_router.post("/payme/callback")
async def payme_callback(payload: dict):
    # Callbackni tekshirish va buyurtma holatini yangilash
    if payload.get("params", {}).get("state") == 1:
        # To'lov muvaffaqiyatli
        return {"result": {"status": "success"}}
    return {"result": {"status": "failed"}}

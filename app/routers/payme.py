from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import logging

# Router yaratish
router = APIRouter()

class PaymeCallbackParams(BaseModel):
    order_id: str
    total_amount: float
    # Payme API uchun kerakli boshqa parametrlar

class PaymeCallbackResult(BaseModel):
    status: str
    message: str

@router.post("/payment/update/")
async def payme_callback(params: PaymeCallbackParams, result: PaymeCallbackResult):
    """
    Payme callbackni qabul qilish va to'lov holatlarini boshqarish.
    """

    if result.status == "created":
        # To'lov yaratildi
        logging.info(f"Transaction created for params: {params} and result: {result}")
        return JSONResponse(status_code=200, content={"status": "success", "message": "Transaction created."})

    elif result.status == "success":
        # To'lov muvaffaqiyatli amalga oshirildi
        logging.info(f"Transaction successfully performed for params: {params} and result: {result}")
        return JSONResponse(status_code=200, content={"status": "success", "message": "Payment successful."})

    elif result.status == "cancelled":
        # To'lov bekor qilindi
        logging.info(f"Transaction cancelled for params: {params} and result: {result}")
        return JSONResponse(status_code=200, content={"status": "error", "message": "Payment cancelled."})

    else:
        # Noma'lum holat
        raise HTTPException(status_code=400, detail="Unknown status")

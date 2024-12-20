from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Union

router = APIRouter()

# Account model
class Account(BaseModel):
    phone: str = None  # Telefon raqami optional


# Parametrlar uchun umumiy bazaviy klasslar
class CheckPerformTransactionParams(BaseModel):
    amount: int
    account: Account


class CreateTransactionParams(BaseModel):
    id: str
    time: int
    amount: int
    account: Account


class PerformTransactionParams(BaseModel):
    id: str


class CancelTransactionParams(BaseModel):
    id: str


class CheckTransactionParams(BaseModel):
    id: str


class GetStatementParams(BaseModel):
    from_time: int
    to_time: int


class ChangePasswordParams(BaseModel):
    password: str


# Request uchun umumiy format
class JSONRPCRequest(BaseModel):
    jsonrpc: str
    id: int
    method: str
    params: Union[
        CheckPerformTransactionParams,
        CreateTransactionParams,
        PerformTransactionParams,
        CancelTransactionParams,
        CheckTransactionParams,
        GetStatementParams,
        ChangePasswordParams
    ]


@router.post("/payment/update", status_code=200)
async def handle_payment_request(request: JSONRPCRequest):
    """
    Bitta endpoint orqali barcha turdagi JSON-RPC so'rovlarini qabul qilish va
    kerakli javobni qaytarish.
    """
    if request.jsonrpc != "2.0":
        raise HTTPException(status_code=400, detail="Invalid JSON-RPC version.")

    # Success Response Template
    success_response = {
        "jsonrpc": "2.0",
        "id": request.id,
        "result": {
            "id": "1288",  # Real response'dan olgan ID
            "time": 1399114284039,  # Real response'dan olgan time
            "receivers": [
                {
                    "id": "5305e3bab097f420a62ced0b",  # Receiver ID
                    "amount": 500000  # Amount for receiver
                }
            ]
        }
    }

    # Error Response Template
    error_response = {
        "jsonrpc": "2.0",
        "id": request.id,
        "error": {
            "code": -31050,
            "message": {
                "ru": "Номер телефона не найден",
                "uz": "Raqam ro'yhatda yo'q",
                "en": "Phone number not found"
            },
            "data": "phone"
        }
    }

    # CheckPerformTransaction logikasi
    if request.method == "CheckPerformTransaction":
        success_response["result"]["message"] = "Transaction checked."
        return JSONResponse(status_code=200, content=success_response)

    # CreateTransaction logikasi
    elif request.method == "CreateTransaction":
        success_response["result"]["message"] = "Transaction created."
        return JSONResponse(status_code=200, content=success_response)

    # PerformTransaction logikasi
    elif request.method == "PerformTransaction":
        success_response["result"]["message"] = "Transaction performed."
        return JSONResponse(status_code=200, content=success_response)

    # CancelTransaction logikasi
    elif request.method == "CancelTransaction":
        success_response["result"]["message"] = "Transaction cancelled."
        return JSONResponse(status_code=200, content=success_response)

    # CheckTransaction logikasi
    elif request.method == "CheckTransaction":
        success_response["result"]["message"] = "Transaction checked."
        return JSONResponse(status_code=200, content=success_response)

    # GetStatement logikasi
    elif request.method == "GetStatement":
        success_response["result"]["message"] = "Statement generated."
        return JSONResponse(status_code=200, content=success_response)

    # ChangePassword logikasi
    elif request.method == "ChangePassword":
        success_response["result"]["message"] = "Password changed."
        return JSONResponse(status_code=200, content=success_response)

    else:
        # Agar method noto'g'ri bo'lsa
        return JSONResponse(status_code=400, content=error_response)

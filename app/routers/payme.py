import uuid
from urllib.request import Request
from fastapi import APIRouter, HTTPException

from app.schemas import Account, CheckPerformTransactionRequest
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


@payme_router.post("/check")
async def check_perform_transaction(request: dict):
    # Parsing JSON-RPC request parameters
    jsonrpc = request.get("jsonrpc")
    request_id = request.get("id")
    method = request.get("method")
    params = request.get("params")

    # Check if the method is CheckPerformTransaction
    if method != "CheckPerformTransaction":
        raise HTTPException(status_code=400, detail="Invalid method")

    # Extract parameters
    amount = params.get("amount")
    account = params.get("account")

    # Basic validation of amount and account
    if not amount or amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")

    if not account or not account.get("account_number"):
        raise HTTPException(status_code=400, detail="Invalid account information")

    # Perform transaction check logic
    transaction_id = str(uuid.uuid4())  # Generate a unique transaction ID

    # Simulate a success response (you can integrate with a payment gateway here)
    response = {
        "jsonrpc": jsonrpc,
        "id": request_id,
        "result": {
            "status": "success",
            "message": "To'lovni amalga oshirishga ruxsat berildi.",
            "transaction_id": transaction_id
        }
    }

    return response
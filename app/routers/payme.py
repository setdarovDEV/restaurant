import os
import base64
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.models import PaymeTransactions, Order
from app.database import get_db
from dotenv import load_dotenv
import logging

load_dotenv()

PAYME_ID = os.getenv("PAYME_MERCHANT_ID")
PAYME_KEY = os.getenv("PAYME_SECRET_KEY")

router = APIRouter()

# Loglashni sozlash
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def format_rpc_error(code, message, request_id):
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {
            "code": code,
            "message": message
        }
    }


logger = logging.getLogger("app.routers.payme")

async def check_authorization(request: Request, request_id):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Basic "):
        return format_rpc_error(
            code=-32504,
            message="Unauthorized",
            request_id=request_id
        )

    # To'g'ri base64 kodlashni tekshirish
    expected_key = base64.b64encode(f"{PAYME_ID}:{PAYME_KEY}".encode()).decode()
    provided_key = auth_header.split(" ")[1]

    # Loglash: Har ikkala kalitni tekshirib chiqamiz
    logger.info(f"Expected Key: {expected_key}")
    logger.info(f"Provided Key: {provided_key}")

    if provided_key != expected_key:
        return format_rpc_error(
            code=-32504,
            message="Invalid Authorization Key",
            request_id=request_id
        )

@router.post("/handle")
async def handle_payme(request: Request, db: Session = Depends(get_db)):
    # So'rovni o'qish
    payload = await request.json()
    method = payload.get("method")
    params = payload.get("params")
    request_id = payload.get("id")

    # Loglash
    logger.info(f"Received request: {method}, Params: {params}, Request ID: {request_id}")

    # Authorizationni tekshirish
    auth_error = await check_authorization(request, request_id)
    if auth_error:
        logger.error(f"Authorization failed: {auth_error}")
        return auth_error

    # Metodlarni tekshirish va ishlov berish
    if method == "CheckPerformTransaction":
        # "CheckPerformTransaction" uchun hech qanday xatolik bo'lmaydi, faqat ruxsat beriladi
        logger.info(f"Checking perform transaction for request ID {request_id}")
        return {"jsonrpc": "2.0", "id": request_id, "result": {"allow": True}}

    elif method == "PerformTransaction":
        try:
            # Tranzaksiya parametrlarini tekshirish
            transaction_id = params.get("id")
            order_id = params["account"].get("order_id")
            amount = params.get("amount")

            if not transaction_id or not order_id or not amount:
                logger.error(f"Missing required parameters in PerformTransaction: {params}")
                return format_rpc_error(
                    code=-31001,  # Parametrlar noto'g'ri yoki etishmayapti
                    message="Invalid parameters",
                    request_id=request_id
                )

            logger.info(
                f"Processing PerformTransaction: Transaction ID: {transaction_id}, Order ID: {order_id}, Amount: {amount}")
            transaction = PaymeTransactions(
                transaction_id=transaction_id,
                account_id=order_id,
                amount=amount,
                state="PROCESSING",  # Bu holatni to'g'ri belgilash
            )
            db.add(transaction)
            db.commit()
            logger.info(f"Transaction processed successfully: {transaction.transaction_id}")
            return {"jsonrpc": "2.0", "id": request_id,
                    "result": {"transaction": transaction.transaction_id, "state": 1}}  # State = 1

        except Exception as e:
            logger.error(f"Error in PerformTransaction: {str(e)}")
            return format_rpc_error(
                code=-31001,
                message="Error processing transaction",
                request_id=request_id
            )

    elif method == "CancelTransaction":
        try:
            transaction = db.query(PaymeTransactions).filter_by(transaction_id=params["id"]).first()
            if not transaction:
                logger.error(f"Transaction not found: {params['id']}")
                return format_rpc_error(
                    code=-31003,
                    message="Transaction not found",
                    request_id=request_id
                )
            transaction.state = "CANCELLED"
            db.commit()
            logger.info(f"Transaction {params['id']} cancelled successfully")
            return {"jsonrpc": "2.0", "id": request_id,
                    "result": {"state": -1}}  # State = -1 for cancelled transactions

        except Exception as e:
            logger.error(f"Error in CancelTransaction: {str(e)}")
            return format_rpc_error(
                code=-31001,
                message="Error cancelling transaction",
                request_id=request_id
            )

    else:
        logger.error(f"Method not found: {method}")
        return format_rpc_error(
            code=-32601,
            message="Method not found",
            request_id=request_id
        )

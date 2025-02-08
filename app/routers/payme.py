from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Order, PaymeTransactions
from app.settings import PaymeConfig
import logging
import base64
import requests
import time

payme_router = APIRouter()
logger = logging.getLogger("payme")

print(f"Loaded PAYME_MERCHANT_ID: {PaymeConfig.MERCHANT_ID}")
print(f"Loaded PAYME_SECRET_KEY: {PaymeConfig.SECRET_KEY}")

class PaymeHelper:
    endpoint = "https://checkout.paycom.uz/api"

    def __init__(self, data):
        self.data = data
        self.transaction_id = data.get("id", None)
        self.timestamp = int(time.time())
        self.auth_header = self.get_auth_header()

    @staticmethod
    def get_auth_header():
        auth_string = f"{PaymeConfig.MERCHANT_ID}:{PaymeConfig.SECRET_KEY}"
        auth_bytes = auth_string.encode("utf-8")
        auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")
        return {"Authorization": f"Basic {auth_base64}"}

    def send_request(self, method, params):
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": self.timestamp
        }
        response = requests.post(self.endpoint, json=payload, headers=self.auth_header)
        return response.json()


from fastapi.security import HTTPBasic, HTTPBasicCredentials
import base64

security = HTTPBasic()

@payme_router.post("/webhook")
async def payme_webhook(request: Request, db: Session = Depends(get_db)):
    params = await request.json()
    logger.info(f"Kelgan so‘rov: {params}")

    auth_header = request.headers.get("Authorization")  # 🚀 `Authorization` headerni olamiz
    logger.info(f"Received Authorization header: {auth_header}")

    # 🔹 Basic Auth tekshirish
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Basic "):
        logger.error("Authorization header not found or incorrect format")
        return {
            "jsonrpc": "2.0",
            "id": params.get("id", None),
            "error": {"code": -32504, "message": "Authentication failed"}
        }

    # 🔹 Base64 kodlangan login va parolni dekod qilish
    try:
        auth_decoded = base64.b64decode(auth_header.split(" ")[1]).decode()
        logger.info(f"Decoded Auth Header: {auth_decoded}")

        if ":" not in auth_decoded:
            raise ValueError("Invalid Basic Auth format")

        username, password = auth_decoded.split(":", 1)
    except Exception as e:
        logger.error(f"Basic Auth decoding error: {e}")
        return {
            "jsonrpc": "2.0",
            "id": params.get("id", None),
            "error": {"code": -32504, "message": "Invalid Basic Auth format"}
        }

    auth_decoded = base64.b64decode(auth_header.split(" ")[1]).decode()
    logger.info(f"Decoded Auth Header: {auth_decoded}")

    if ":" not in auth_decoded:
        raise ValueError("Invalid Basic Auth format")

    username, password = auth_decoded.split(":", 1)

    logger.info(f"Received MERCHANT_ID: {username}, Expected: {PaymeConfig.MERCHANT_ID}")
    logger.info(f"Received SECRET_KEY: {password}, Expected: {PaymeConfig.SECRET_KEY}")

    merchant_id = PaymeConfig().MERCHANT_ID  # `.()` bilan obyekt yaratib chaqiramiz
    secret_key = PaymeConfig().SECRET_KEY

    if username != merchant_id or password != secret_key:
        logger.error("Invalid credentials used")
        return {
            "jsonrpc": "2.0",
            "id": params.get("id", None),
            "error": {"code": -32504, "message": "Invalid credentials"}
        }

    return {"jsonrpc": "2.0", "id": params.get("id", None), "result": "Authentication success"}


async def check_perform_transaction(params: dict, db: Session):
    """ Payme CheckPerformTransaction """

    amount = float(params["params"].get("amount", 0))
    account = params["params"].get("account", {})

    # 🔹 1. Buyurtmani bazadan olish
    order_id = account.get("order_id")
    order = db.query(Order).filter_by(id=order_id).first()

    if not order:
        return {
            "error": {
                "code": -31050,
                "message": "Order not found"
            }
        }

    # 🔹 2. Faqat `PENDING` statusdagi buyurtmalarni qabul qilish
    if order.status != "PENDING":
        return {
            "error": {
                "code": -31008,
                "message": "Transaction not allowed for this order status"
            }
        }

    # 🔹 3. To‘lov summasi to‘g‘ri ekanligini tekshiramiz
    expected_amount = float(order.price)

    if amount != expected_amount:
        return {
            "error": {
                "code": -31001,
                "message": "Invalid amount"
            }
        }

    # ✅ Hammasi to‘g‘ri bo‘lsa, tranzaksiya mumkinligini tasdiqlaymiz
    return {"allow": True}


async def create_transaction(params: dict, db: Session):
    transaction_id = params["params"].get("id")
    amount = params["params"].get("amount")

    existing_transaction = db.query(PaymeTransactions).filter_by(transaction_id=transaction_id).first()
    if existing_transaction:
        return {"error": {"code": -31004, "message": "Transaction already exists"}}

    new_transaction = PaymeTransactions(
        transaction_id=transaction_id,
        amount=amount,
        status=1
    )
    db.add(new_transaction)
    db.commit()

    return {
        "create_time": int(new_transaction.created_at.timestamp()),
        "transaction": transaction_id,
        "state": new_transaction.status
    }


async def perform_transaction(params: dict, db: Session):
    transaction_id = params["params"].get("id")
    transaction = db.query(PaymeTransactions).filter_by(transaction_id=transaction_id).first()
    if not transaction:
        return {"error": {"code": -31003, "message": "Transaction not found"}}

    transaction.status = 2
    db.commit()

    return {"perform_time": int(transaction.updated_at.timestamp()), "state": 2}


async def cancel_transaction(params: dict, db: Session):
    transaction_id = params["params"].get("id")
    transaction = db.query(PaymeTransactions).filter_by(transaction_id=transaction_id).first()
    if not transaction:
        return {"error": {"code": -31003, "message": "Transaction not found"}}

    transaction.status = 3
    db.commit()

    return {"cancel_time": int(transaction.updated_at.timestamp()), "state": 3}


async def check_transaction(params: dict, db: Session):
    transaction_id = params["params"].get("id")
    transaction = db.query(PaymeTransactions).filter_by(transaction_id=transaction_id).first()

    if not transaction:
        return {"error": {"code": -31003, "message": "Transaction not found"}}

    return {
        "create_time": int(transaction.created_at.timestamp()),
        "state": transaction.status
    }

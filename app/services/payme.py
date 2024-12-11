import hashlib
import json
import requests
from fastapi import HTTPException
from typing import Dict

class PaymeClient:
    def __init__(self, merchant_id: str, secret_key: str, test_mode: bool = True):
        self.merchant_id = merchant_id
        self.secret_key = secret_key
        self.base_url = "https://checkout.test.paycom.uz/api" if test_mode else "https://checkout.paycom.uz/api"

    def _generate_signature(self, params: Dict) -> str:
        # JSON string yaratib, SHA1 hash hisoblash
        # Parametrlar JSON formatida tartiblangan bo'lishi kerak
        sorted_params = json.dumps(params, separators=(',', ':'))
        return hashlib.sha1((sorted_params + self.secret_key).encode()).hexdigest()

    def create_invoice(self, amount: int, order_id: str) -> Dict:
        payload = {
            "method": "CreateTransaction",
            "params": {
                "amount": amount * 100,  # Tiyin ko‘rinishiga aylantirish
                "account": {"order_id": order_id},
            }
        }
        signature = self._generate_signature(payload)
        headers = {"X-Auth": f"{self.merchant_id}:{signature}"}

        response = requests.post(self.base_url, json=payload, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        return response.json()

    def check_payment_status(self, transaction_id: str) -> Dict:
        payload = {
            "method": "CheckTransaction",
            "params": {"id": transaction_id}
        }
        signature = self._generate_signature(payload)
        headers = {"X-Auth": f"{self.merchant_id}:{signature}"}

        response = requests.post(self.base_url, json=payload, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        return response.json()

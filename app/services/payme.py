import httpx
from app.settings import PayMeSettings


class PayMeService:
    @staticmethod
    async def create_transaction(amount: int, order_id: str):
        headers = {"Content-Type": "application/json"}
        payload = {
            "method": "CreateTransaction",
            "params": {
                "amount": amount * 100,  # Tiyinlarda berilishi kerak
                "account": {"order_id": order_id},
            }
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{PayMeSettings.BASE_URL}/api",
                headers=headers,
                json=payload,
                auth=(PayMeSettings.MERCHANT_ID, PayMeSettings.SECRET_KEY)
            )
            return response.json()
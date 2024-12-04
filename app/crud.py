from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func
from app.models import Order, Reservation
import qrcode
import os

async def get_all_orders(db: AsyncSession):
    # Execute the query
    result = await db.execute(select(Order))
    # Fetch all rows
    orders = result.scalars().all()  # Returns a list of Order objects
    return orders

async def get_single_order(db: AsyncSession, order_id: int):
    # Execute the query with a filter
    result = await db.execute(select(Order).where(Order.id == order_id))
    # Fetch a single row
    order = result.scalars().first()  # Returns a single Order object or None
    return order

async def get_order_count(db: AsyncSession):
    result = await db.execute(select(func.count(Order.id)))
    count = result.scalar()  # Fetches the scalar result (e.g., the count)
    return count or 0  # Return 0 if the result is None

# Example of another aggregate query (total revenue)
async def get_total_revenue(db: AsyncSession):
    result = await db.execute(select(func.sum(Order.price)))  # Summing the prices
    return result.scalar() or 0  # Get the sum, or 0 if no result


async def get_total_reservations(db: AsyncSession):
    result = await db.execute(select(func.count(Reservation.id)))
    return result.scalar() or 0

def generate_qr_code_file(table_id: int):
    # Local yoki domen URLini config fayldan olish
    domain = os.getenv("DOMAIN_URL", "http://127.0.0.1:8000")  # default to local URL
    url = f"{domain}/tables/{table_id}"

    # QR kodni yaratish
    img = qrcode.make(url)

    # Fayl nomini yaratish
    file_path = f"temp_qr_codes/table_{table_id}.png"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    img.save(file_path)

    return file_path
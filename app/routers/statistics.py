from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.permission import is_nazoratchi
from sqlalchemy import func, extract
from app.models import Order, Reservation
from datetime import datetime, timedelta, date
from app.schemas import TotalRevenueResponse, TableRevenueResponse, PeriodicRevenueResponse, OrderStatus

statistics_router = APIRouter()

# Jami daromadni olish
@statistics_router.get("/{business_id}/total-revenue", response_model=TotalRevenueResponse, dependencies=[Depends(is_nazoratchi)])
def get_total_revenue(business_id: int, db: Session = Depends(get_db)):
    total_revenue = db.query(func.sum(Order.price)).filter(
        Order.business_id == business_id,
        Order.status == OrderStatus.COMPLETED  # ✅ Faqat yakunlangan buyurtmalar
    ).scalar() or 0.0

    return {"total_revenue": total_revenue}

# Har stol bo'yicha daromad olish
@statistics_router.get("/{business_id}/table-revenue/{table_id}", response_model=TableRevenueResponse, dependencies=[Depends(is_nazoratchi)])
def get_table_revenue(business_id: int, table_id: int, db: Session = Depends(get_db)):
    table_revenue = db.query(func.sum(Order.price)).filter(
        Order.business_id == business_id,
        Order.table_id == table_id,
        Order.status == OrderStatus.COMPLETED
    ).scalar() or 0.0

    return {"table_revenue": table_revenue}

# Kundalik daromad
@statistics_router.get("/{business_id}/revenue", response_model=PeriodicRevenueResponse,
                       dependencies=[Depends(is_nazoratchi)])
def get_revenue_by_dates(
    business_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    period: Optional[str] = None,
    db: Session = Depends(get_db)
):
    now = datetime.utcnow()

    # 📌 Agar `period` ko‘rsatilgan bo‘lsa, avtomatik sanalarni belgilash
    if period:
        if period == "daily":
            start_date = now - timedelta(days=1)
        elif period == "weekly":
            start_date = now - timedelta(weeks=1)
        elif period == "monthly":
            start_date = now - timedelta(days=30)
        elif period == "yearly":
            start_date = now - timedelta(days=365)
        else:
            raise HTTPException(status_code=400, detail="Invalid period. Choose daily, weekly, monthly, or yearly.")

    # 📌 Foydalanuvchi start_date va end_date kiritmagan bo‘lsa, default qilib bugungi sanani olish
    if not start_date:
        start_date = now - timedelta(days=30)  # ✅ Default 30 kunlik hisobot
    if not end_date:
        end_date = now  # ✅ Hozirgi vaqt

    # 📌 Sana formatini tekshirish
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be earlier than end_date")

    # 📌 Faqat **COMPLETED** buyurtmalarni hisoblash
    revenue = db.query(func.sum(Order.price)).filter(
        Order.business_id == business_id,
        Order.status == OrderStatus.COMPLETED,
        Order.created_at >= start_date,
        Order.created_at <= end_date
    ).scalar() or 0.0

    return {"revenue": revenue}



@statistics_router.get("/{business_id}/detailed-statistics", tags=["Statistics"])
def get_detailed_statistics(
    business_id: int,
    year: int = None,
    month: int = None,
    db: Session = Depends(get_db)
):
    try:
        # 📌 `business_id` bo‘yicha filtrlash
        filters = [Order.business_id == business_id]

        # 📌 Yillik yoki oylik filtrni qo‘shish
        if year:
            filters.append(extract('year', Order.created_at) == year)
        if month:
            filters.append(extract('month', Order.created_at) == month)

        # 📌 Umumiy yoki filtrlangan daromadni hisoblash
        total_revenue = (
            db.query(func.sum(Order.price))
            .filter(*filters, Order.status == OrderStatus.COMPLETED)  # ✅ Faqat to‘langan buyurtmalar
            .scalar() or 0
        )

        # 📌 Sotilgan mahsulotlar sonini hisoblash
        total_items_sold = (
            db.query(func.sum(Order.quantity))
            .filter(*filters, Order.status == OrderStatus.COMPLETED)
            .scalar() or 0
        )

        # 📌 Buyurtmalar sonini hisoblash
        total_orders = (
            db.query(func.count(Order.id))
            .filter(*filters)
            .scalar() or 0
        )

        # 📌 Rezervatsiyalar sonini hisoblash (business_id qo‘shildi)
        total_reservations = (
            db.query(func.count(Reservation.id))
            .filter(Reservation.business_id == business_id, *filters)
            .scalar() or 0
        )

        return {
            "total_revenue": total_revenue,
            "total_items_sold": total_items_sold,
            "total_orders": total_orders,
            "total_reservations": total_reservations,
        }
    except Exception as e:
        return {"error": str(e)}

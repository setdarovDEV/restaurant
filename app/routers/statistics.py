from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.permission import is_nazoratchi
from sqlalchemy import func, extract
from app.models import Order, Reservation
from datetime import datetime, timedelta
from app.schemas import TotalRevenueResponse, TableRevenueResponse, PeriodicRevenueResponse

statistics_router = APIRouter()

# Jami daromadni olish
@statistics_router.get("/total_revenue", response_model=TotalRevenueResponse, dependencies=[Depends(is_nazoratchi)])
async def get_total_revenue(db: Session = Depends(get_db)):
    total_revenue = db.query(func.sum(Order.quantity * Order.price)).scalar()
    return {"total_revenue": total_revenue or 0.0}

# Har stol bo'yicha daromad olish
@statistics_router.get("/table_revenue/{table_id}", response_model=TableRevenueResponse, dependencies=[Depends(is_nazoratchi)])
async def get_table_revenue(table_id: int, db: Session = Depends(get_db)):
    table_revenue = db.query(func.sum(Order.quantity * Order.price)).filter(Order.table_id == table_id).scalar()
    return {"table_revenue": table_revenue or 0.0}

# Kundalik daromad
@statistics_router.get("/daily_revenue", response_model=PeriodicRevenueResponse, dependencies=[Depends(is_nazoratchi)])
async def get_daily_revenue(db: Session = Depends(get_db)):
    today = datetime.utcnow().date()
    daily_revenue = db.query(func.sum(Order.quantity * Order.price)).filter(func.date(Order.created_at) == today).scalar()
    return {"revenue": daily_revenue or 0.0}

# Haftalik daromad
@statistics_router.get("/weekly_revenue", response_model=PeriodicRevenueResponse, dependencies=[Depends(is_nazoratchi)])
async def get_weekly_revenue(db: Session = Depends(get_db)):
    today = datetime.utcnow().date()
    one_week_ago = today - timedelta(weeks=1)
    weekly_revenue = db.query(func.sum(Order.quantity * Order.price)).filter(Order.created_at.between(one_week_ago, today)).scalar()
    return {"revenue": weekly_revenue or 0.0}

# Oylik daromad
@statistics_router.get("/monthly_revenue", response_model=PeriodicRevenueResponse, dependencies=[Depends(is_nazoratchi)])
async def get_monthly_revenue(db: Session = Depends(get_db)):
    today = datetime.utcnow().date()
    one_month_ago = today - timedelta(days=30)
    monthly_revenue = db.query(func.sum(Order.quantity * Order.price)).filter(Order.created_at.between(one_month_ago, today)).scalar()
    return {"revenue": monthly_revenue or 0.0}

# Yillik daromad
@statistics_router.get("/yearly_revenue", response_model=PeriodicRevenueResponse, dependencies=[Depends(is_nazoratchi)])
async def get_yearly_revenue(db: Session = Depends(get_db)):
    today = datetime.utcnow().date()
    one_year_ago = today - timedelta(days=365)
    yearly_revenue = db.query(func.sum(Order.quantity * Order.price)).filter(Order.created_at.between(one_year_ago, today)).scalar()
    return {"revenue": yearly_revenue or 0.0}


@statistics_router.get("/detailed-statistics", tags=["Statistics"])
def get_detailed_statistics(
    year: int = None,
    month: int = None,
    db: Session = Depends(get_db)
):
    try:
        # Faqat ma'lum yillik yoki oylik statistikani olish uchun filtr qo'llash
        filters = []
        if year:
            filters.append(extract('year', Order.created_at) == year)
        if month:
            filters.append(extract('month', Order.created_at) == month)

        # Umumiy yoki filtrlangan daromadni hisoblash
        total_revenue = (
            db.query(func.sum(Order.price))
            .filter(*filters)
            .scalar() or 0
        )

        # Sotilgan mahsulotlar sonini hisoblash
        total_items_sold = (
            db.query(func.sum(Order.quantity))
            .filter(*filters)
            .scalar() or 0
        )

        # Buyurtmalar sonini hisoblash
        total_orders = (
            db.query(func.count(Order.id))
            .filter(*filters)
            .scalar() or 0
        )

        # Rezervatsiyalar sonini hisoblash
        total_reservations = (
            db.query(func.count(Reservation.id))
            .filter(*filters)
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
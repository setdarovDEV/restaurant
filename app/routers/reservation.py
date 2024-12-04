import pytz
from fastapi import BackgroundTasks, APIRouter, HTTPException, Depends, status
from fastapi_jwt_auth import AuthJWT
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Reservation, Table
from app.schemas import ReservationCreate, ReservationResponse, ReservationUpdate, TableStatus
from datetime import timezone
from typing import List
import asyncio
from datetime import datetime
import time
from app.permission import is_nazoratchi, is_user, is_afissant  # Rollar uchun ruxsatlarni import qilish

reservation_router = APIRouter()

# Toshkent vaqt zonasini o'rnatish
TASHKENT_TZ = pytz.timezone("Asia/Tashkent")


def convert_to_tashkent_timezone(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.UTC)
    return dt.astimezone(TASHKENT_TZ)


# Stol holatini AVAILABLE ga o'zgartirish funksiyasi
def set_table_status_to_available(table: Table, db: Session):
    table.status = TableStatus.AVAILABLE
    db.add(table)
    db.commit()


# Stol holatini RESERVED ga o'zgartirish funksiyasi
def set_table_status_to_reserved(table: Table, db: Session):
    table.status = TableStatus.RESERVED
    db.add(table)
    db.commit()


# Rezervatsiya yaratish - faqat USER va AFISSANT yaratishi mumkin
@reservation_router.post("/create", response_model=ReservationResponse)
async def create_reservation(reservation: ReservationCreate, background_tasks: BackgroundTasks,
                             db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Enter valid access token")

    # start_time va end_time ni Toshkent vaqt zonasiga o'tkazish
    start_time = convert_to_tashkent_timezone(reservation.start_time)
    end_time = convert_to_tashkent_timezone(reservation.end_time)

    # Reservation modelini yaratish
    db_reservation = Reservation(
        user_id=reservation.user_id,
        table_id=reservation.table_id,
        start_time=start_time,
        end_time=end_time,
        is_active=True
    )
    db.add(db_reservation)
    db.commit()
    db.refresh(db_reservation)

    # Stolni olish va start_time va end_time vaqtini tekshirish
    table = db.query(Table).filter(Table.id == reservation.table_id).first()

    # Agar start_time yetib kelsa, stol holatini RESERVED ga o'tkazish
    if start_time <= datetime.now(timezone.utc):
        set_table_status_to_reserved(table, db)
    else:
        delay_until_start = (start_time - datetime.now(timezone.utc)).total_seconds()
        background_tasks.add_task(time.sleep, delay_until_start)
        background_tasks.add_task(set_table_status_to_reserved, table, db)

    # end_time o'tgandan keyin AVAILABLE ga o'tkazish
    delay_until_end = (end_time - datetime.now(timezone.utc)).total_seconds()
    background_tasks.add_task(time.sleep, delay_until_end)
    background_tasks.add_task(set_table_status_to_available, table, db)

    return db_reservation


# Rezervatsiyalarni olish - faqat AFISSANT ko'rishi mumkin
@reservation_router.get("/", response_model=List[ReservationResponse], dependencies=[Depends(is_afissant)])
def get_reservations(db: Session = Depends(get_db)):
    return db.query(Reservation).all()


# Rezervatsiyani yangilash - faqat NAZORATCHI yangilashi mumkin
@reservation_router.put("/{id}", response_model=ReservationResponse, dependencies=[Depends(is_nazoratchi)])
def update_reservation(id: int, reservation: ReservationUpdate, db: Session = Depends(get_db)):
    db_reservation = db.query(Reservation).filter(Reservation.id == id).first()
    if db_reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")
    for key, value in reservation.dict().items():
        setattr(db_reservation, key, value)
    db.commit()
    db.refresh(db_reservation)
    return db_reservation


# Rezervatsiyani o'chirish - faqat NAZORATCHI o'chirishi mumkin
@reservation_router.delete("/{id}", response_model=ReservationResponse, dependencies=[Depends(is_nazoratchi)])
def delete_reservation(id: int, db: Session = Depends(get_db)):
    db_reservation = db.query(Reservation).filter(Reservation.id == id).first()
    if db_reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")
    db.delete(db_reservation)
    db.commit()
    return db_reservation

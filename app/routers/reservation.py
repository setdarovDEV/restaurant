import pytz
from fastapi import BackgroundTasks, APIRouter, HTTPException, Depends, status
from fastapi_jwt_auth import AuthJWT
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Reservation, Table
from app.schemas import ReservationCreate, ReservationResponse, ReservationUpdate, TableStatus, TableInDB, \
    ReservationPatch
from datetime import timezone, datetime
from typing import List
import time
from app.permission import is_nazoratchi, is_user, is_afissant

reservation_router = APIRouter()

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


TASHKENT_TZ = pytz.timezone("Asia/Tashkent")

def combine_datetime(day: datetime.date, time_str: str) -> datetime:
    """ Kun va vaqtni birlashtirib, to‘liq datetime yaratadi """
    hour, minute = map(int, time_str.split(":"))
    return datetime.combine(day, time(hour=hour, minute=minute), tzinfo=TASHKENT_TZ)


@reservation_router.post("/{business_id}/create", response_model=ReservationResponse)
async def create_reservation(
    business_id: int,
    reservation: ReservationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    Authorize: AuthJWT = Depends()
):
    try:
        Authorize.jwt_required()
        current_user_id = int(Authorize.get_jwt_subject())  # Token orqali foydalanuvchi ID sini olish
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Enter valid access token")

    # 🛠 `day` maydoni allaqachon `datetime.date`, unga o'zgartirish kerak emas
    day = reservation.day  # `reservation.day` ni bevosita `date` sifatida ishlatamiz

    # 🛠 `start_time` va `end_time` ni `datetime.time` obyektiga o‘tkazish
    start_time = datetime.strptime(reservation.start_time, "%H:%M").time()
    end_time = datetime.strptime(reservation.end_time, "%H:%M").time()

    # 🛠 To‘liq `datetime` formatiga o‘tkazish
    start_datetime = datetime.combine(day, start_time)
    end_datetime = datetime.combine(day, end_time)

    # 🛠 Stolni tekshirish
    table = db.query(Table).filter(Table.id == reservation.table_id, Table.business_id == business_id).first()
    if not table:
        raise HTTPException(status_code=404, detail="Table not found for this business")

    # 🛠 Stol bandligini tekshirish
    existing_reservation = db.query(Reservation).filter(
        Reservation.table_id == reservation.table_id,
        Reservation.business_id == business_id,
        Reservation.start_time < end_datetime,
        Reservation.end_time > start_datetime
    ).first()

    if existing_reservation:
        raise HTTPException(status_code=400, detail="Table is already reserved for this time slot")

    # 🛠 Reservation modelini yaratish
    db_reservation = Reservation(
        user_id=current_user_id,  # Token orqali olingan user_id
        table_id=reservation.table_id,
        start_time=start_datetime,
        end_time=end_datetime,
        is_active=True,
        business_id=business_id
    )
    db.add(db_reservation)
    db.commit()
    db.refresh(db_reservation)

    # 🛠 Agar start_time yetib kelsa, stol holatini RESERVED ga o'tkazish
    if start_datetime <= datetime.now():
        set_table_status_to_reserved(table, db)
    else:
        delay_until_start = (start_datetime - datetime.now()).total_seconds()
        background_tasks.add_task(time.sleep, delay_until_start)
        background_tasks.add_task(set_table_status_to_reserved, table, db)

    # 🛠 end_time o'tgandan keyin AVAILABLE ga o'tkazish
    delay_until_end = (end_datetime - datetime.now()).total_seconds()
    background_tasks.add_task(time.sleep, delay_until_end)
    background_tasks.add_task(set_table_status_to_available, table, db)

    return db_reservation


# 🔹 Foydalanuvchi faqat o‘zi qilgan rezervatsiyalar tarixini ko‘rishi mumkin
@reservation_router.get("/{business_id}/history", response_model=List[ReservationResponse])
def get_my_reservations(business_id: int, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
        current_user_id = int(Authorize.get_jwt_subject())  # Token orqali foydalanuvchi ID sini olish
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Enter valid access token")

    # 📌 **Faqat `is_active=False` bo‘lgan rezervatsiyalarni chiqarish**
    reservations = db.query(Reservation).filter(
        Reservation.user_id == current_user_id,
        Reservation.business_id == business_id,
        Reservation.is_active == True  # 📌 Faqat aktiv bo'lmagan (yopilgan) rezervatsiyalar
    ).all()

    # 📌 Har bir rezervatsiya uchun stol ma'lumotlarini qo‘shish
    for reservation in reservations:
        table = db.query(Table).filter(Table.id == reservation.table_id).first()
        reservation.table = table if table else TableInDB(
            id=0,
            table_number=0,
            description="Table information not available",
            capacity=0,
            status="UNKNOWN",
            module_id=0,
            business_id=business_id
        )

    return reservations



# 🔹 Foydalanuvchi faqat **hozirgi aktiv rezervatsiyalarini** ko‘rishi mumkin
@reservation_router.get("/{business_id}/active", response_model=List[ReservationResponse])
def get_my_active_reservations(business_id: int, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
        current_user_id = int(Authorize.get_jwt_subject())  # Token orqali foydalanuvchi ID sini olish
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Enter valid access token")

    current_time = datetime.now()  # Hozirgi vaqtni olish

    active_reservations = db.query(Reservation).filter(
        Reservation.user_id == current_user_id,
        Reservation.business_id == business_id,
        Reservation.start_time <= current_time,  # Boshlangan yoki boshlanishi yaqin
        Reservation.end_time > current_time,  # Hali tugamagan
        Reservation.is_active == True  # Aktiv bo‘lgan rezervatsiyalar
    ).all()

    # 📌 Har bir rezervatsiya uchun stol ma'lumotlarini qo‘shish
    for reservation in active_reservations:
        reservation.table = db.query(Table).filter(Table.id == reservation.table_id).first()

    return active_reservations



# 🔹 **Biznesga tegishli barcha rezervatsiyalarni olish - faqat AFISSANT ko‘rishi mumkin**
@reservation_router.get("/{business_id}/history/all", response_model=List[ReservationResponse], dependencies=[Depends(is_afissant)])
def get_all_active_reservations(business_id: int, db: Session = Depends(get_db)):
    return db.query(Reservation).filter(
        Reservation.business_id == business_id,  # ✅ Faqat shu biznesdagi rezervatsiyalar
        Reservation.is_active == True  # ✅ Faqat `active` bo‘lgan rezervatsiyalar
    ).order_by(Reservation.start_time.desc()).all()  # ✅ Eng yangi rezervatsiyalar oldin chiqadi

# 📌 Toshkent vaqt zonasi
TASHKENT_TZ = pytz.timezone("Asia/Tashkent")

@reservation_router.get("/{business_id}/active/all", response_model=List[ReservationResponse], dependencies=[Depends(is_afissant)])
def get_all_current_active_reservations(business_id: int, db: Session = Depends(get_db)):
    current_time = datetime.now(TASHKENT_TZ)  # ✅ Toshkent vaqtini olish

    active_reservations = db.query(Reservation).filter(
        Reservation.business_id == business_id,  # ✅ Faqat shu biznesdagi rezervatsiyalar
        Reservation.is_active == True,  # ✅ Faqat `active` bo‘lgan rezervatsiyalar
        Reservation.start_time <= current_time,  # ✅ Boshlangan yoki boshlanishi yaqin
        Reservation.end_time > current_time  # ✅ Hali tugamagan
    ).order_by(Reservation.start_time.desc()).all()  # ✅ Eng yangi rezervatsiyalar oldin chiqadi

    # 📌 Har bir rezervatsiya uchun stol ma'lumotlarini qo‘shish
    for reservation in active_reservations:
        reservation.table = db.query(Table).filter(Table.id == reservation.table_id).first()

    return active_reservations


# 🔹 **Bitta rezervatsiyani ID orqali olish**
@reservation_router.get("/{business_id}/{reservation_id}", response_model=ReservationResponse, dependencies=[Depends(is_afissant)])
def get_reservation_detail(business_id: int, reservation_id: int, db: Session = Depends(get_db)):
    db_reservation = db.query(Reservation).filter(
        Reservation.id == reservation_id,
        Reservation.business_id == business_id
    ).first()

    if db_reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")

    return db_reservation


@reservation_router.put("/{business_id}/{reservation_id}", response_model=ReservationResponse,
                        dependencies=[Depends(is_afissant)])
def update_reservation(business_id: int, reservation_id: int, reservation: ReservationUpdate,
                       db: Session = Depends(get_db)):
    db_reservation = db.query(Reservation).filter(
        Reservation.id == reservation_id,
        Reservation.business_id == business_id
    ).first()

    if db_reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")

    # 📌 `day`, `start_time` va `end_time` ni datetime obyektiga aylantirish
    start_datetime = datetime.combine(reservation.day, reservation.start_time)
    end_datetime = datetime.combine(reservation.day, reservation.end_time)

    # 📌 Vaqt formatini UTC ga o‘tkazish (Toshkent vaqtida bo‘lsa)
    start_datetime = start_datetime.replace(tzinfo=pytz.utc)
    end_datetime = end_datetime.replace(tzinfo=pytz.utc)

    # 📌 Yangilash
    db_reservation.table_id = reservation.table_number
    db_reservation.start_time = start_datetime
    db_reservation.end_time = end_datetime
    db_reservation.is_active = reservation.is_active

    db.commit()
    db.refresh(db_reservation)
    return db_reservation

TASHKENT_TZ = pytz.timezone("Asia/Tashkent")

@reservation_router.patch("/{business_id}/{reservation_id}", response_model=ReservationResponse,
                          dependencies=[Depends(is_afissant)])
def patch_reservation(business_id: int, reservation_id: int, reservation: ReservationPatch,
                      db: Session = Depends(get_db)):
    db_reservation = db.query(Reservation).filter(
        Reservation.id == reservation_id,
        Reservation.business_id == business_id
    ).first()

    if db_reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")

    # 📌 Agar hech qanday o‘zgarish bo‘lmasa, xatolik chiqaramiz
    if all(v is None for v in reservation.dict().values()):
        raise HTTPException(status_code=400, detail="No fields provided for update.")

    # 📌 Agar `table_number` jo‘natilgan bo‘lsa, yangilaymiz
    if reservation.table_number is not None:
        db_reservation.table_id = reservation.table_number

    # 📌 Agar `start_time` yoki `end_time` jo‘natilgan bo‘lsa, `day` ni olish
    if reservation.start_time or reservation.end_time:
        existing_day = db_reservation.start_time.astimezone(TASHKENT_TZ).date()  # 📌 Eski `day` ni olish

        # 📌 Agar `day` jo‘natilgan bo‘lsa, uni ishlatamiz, aks holda eski sanani ishlatamiz
        day = reservation.day if reservation.day else existing_day

        # 📌 Foydalanuvchi jo‘natgan vaqtlarni ishlatamiz, agar None bo‘lsa, eski qiymat saqlanadi
        start_time = reservation.start_time if reservation.start_time else db_reservation.start_time.astimezone(TASHKENT_TZ).strftime("%H:%M")
        end_time = reservation.end_time if reservation.end_time else db_reservation.end_time.astimezone(TASHKENT_TZ).strftime("%H:%M")

        # 📌 `start_time` va `end_time` ni `datetime` formatiga o‘tkazish
        start_datetime = TASHKENT_TZ.localize(datetime.combine(day, datetime.strptime(start_time, "%H:%M").time()))
        end_datetime = TASHKENT_TZ.localize(datetime.combine(day, datetime.strptime(end_time, "%H:%M").time()))

        # 📌 UTC vaqtiga o‘tkazish (bazada saqlash uchun)
        db_reservation.start_time = start_datetime.astimezone(pytz.utc)
        db_reservation.end_time = end_datetime.astimezone(pytz.utc)

    # 📌 Agar `is_active` jo‘natilgan bo‘lsa, yangilaymiz
    if reservation.is_active is not None:
        db_reservation.is_active = reservation.is_active

    db.commit()
    db.refresh(db_reservation)
    return db_reservation


@reservation_router.delete("/{business_id}/{reservation_id}", response_model=ReservationResponse,
                           dependencies=[Depends(is_afissant)])  # ✅ Faqat NAZORATCHI o‘chira olishi kerak
def delete_reservation(business_id: int, reservation_id: int, db: Session = Depends(get_db)):
    db_reservation = db.query(Reservation).filter(
        Reservation.id == reservation_id,
        Reservation.business_id == business_id
    ).first()

    if db_reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")

    # 📌 `table` obyektini olish
    table = db_reservation.table

    # 📌 Agar `table` mavjud bo‘lsa va `RESERVED` bo‘lsa, statusni `AVAILABLE` qilib o‘zgartiramiz
    if table and table.status == "RESERVED":
        table.status = "AVAILABLE"
        db.add(table)  # ✅ `table` ni bazada saqlaymiz

    db.delete(db_reservation)
    db.commit()

    return db_reservation

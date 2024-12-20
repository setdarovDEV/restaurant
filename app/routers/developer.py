from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_jwt_auth import AuthJWT
from fastapi_utils.tasks import repeat_every
from psycopg2 import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import Session
from app import schemas, models
from app.database import get_db
from app.models import RoleEnum, Business
from app.permission import is_developer
from app.dependencies import get_current_user
from datetime import datetime, timedelta

from app.schemas import BusinessUpdateDays

dev_router = APIRouter()

@dev_router.on_event("startup")
@repeat_every(seconds=60 * 60)  # Har bir soatda ishlaydi
def update_business_is_paid_status(db: Session = Depends(get_db)):
    expired_businesses = db.query(Business).filter(
        Business.is_paid == True,
        Business.payment_expiry_date < datetime.utcnow()
    ).all()

    for business in expired_businesses:
        business.is_paid = False  # Muddati tugagan bizneslarni yangilash
        business.updated_at = datetime.utcnow()

    db.commit()


def hash_password(password: str) -> str:
    return generate_password_hash(password)

def generate_unique_username(base_username: str, db: Session) -> str:
    username = base_username
    counter = 1
    while db.query(models.User).filter(models.User.username == username).first():
        username = f"{base_username}_{counter}"
        counter += 1
    return username

@dev_router.post("/business", response_model=schemas.BusinessResponse, dependencies=[Depends(is_developer)])
async def create_business(
    business: schemas.BusinessCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    expiry_date = None
    if business.is_paid and business.payment_days:
        expiry_date = datetime.utcnow() + timedelta(days=business.payment_days)

    # Biznes yaratish
    new_business = models.Business(
        name=business.name,
        location=business.location,
        image=business.image,
        is_paid=business.is_paid,
        payment_expiry_date=expiry_date,
        developer_id=current_user.id,
    )
    db.add(new_business)
    db.commit()
    db.refresh(new_business)


    return {
        "id": new_business.id,
        "name": new_business.name,
        "location": new_business.location,
        "image": new_business.image,
        "is_paid": new_business.is_paid,
        "payment_expiry_date": new_business.payment_expiry_date,
    }


def hash_password(password: str) -> str:
    return generate_password_hash(password)

@dev_router.post("/{business_id}/user", status_code=201, response_model=schemas.UserResponse, dependencies=[Depends(is_developer)])
async def create_user_for_business(
    business_id: int,
    user: schemas.UserCreate,  # User ma'lumotlari uchun schema
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):

    # Biznesni tekshirish
    business = db.query(models.Business).filter(models.Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    # Yangi foydalanuvchini yaratish
    hashed_password = hash_password(user.password)
    new_user = models.User(
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        phone_number=user.phone_number,
        hashed_password=hashed_password,
        role=models.RoleEnum.NAZORATCHI,  # Nazoratchi bo'lishi ko'zda tutilgan
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Foydalanuvchini biznesga bog'lash
    business.nazoratchi_id = new_user.id
    db.commit()
    db.refresh(business)

    return {
        "message": "User created and linked to the business successfully",
        "user": new_user,
        "business": business,
    }


@dev_router.put("/business/{business_id}", status_code=200, dependencies=[Depends(is_developer)])
async def update_business(business_id: int, update_data: BusinessUpdateDays, db: Session = Depends(get_db), current_user=Depends(get_current_user)):

    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    if update_data.additional_days <= 0:
        raise HTTPException(status_code=400, detail="Additional days cannot be negative")

    if business.payment_expiry_date:
        business.payment_expiry_date += timedelta(days=update_data.additional_days)
    else:
        business.payment_expiry_date = datetime.utcnow() + timedelta(days=update_data.additional_days)

    business.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(business)
    return {
        "message": "Business days extended successfully",
        "business": business,
    }

@dev_router.get("/", dependencies=[Depends(is_developer)])
async def get_business(Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    business = db.query(Business).all()
    return business
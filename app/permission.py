from fastapi import HTTPException, Depends
from fastapi_jwt_auth import AuthJWT
from sqlalchemy.orm import Session
from app.models import User
from app.database import SessionLocal
from typing import Optional


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Foydalanuvchi rolini olish
def get_current_user(Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
        user_role = Authorize.get_raw_jwt().get("role")
        return user_role
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid or missing token")

# NAZORATCHI ruxsati
def is_nazoratchi(Authorize: AuthJWT = Depends()):
    user_role = get_current_user(Authorize)
    if user_role != "NAZORATCHI":
        raise HTTPException(status_code=403, detail="Access forbidden: Insufficient permissions")

# AFISSANT ruxsati
def is_afissant(Authorize: AuthJWT = Depends()):
    user_role = get_current_user(Authorize)
    if user_role != "AFISSANT":
        raise HTTPException(status_code=403, detail="Access forbidden: Insufficient permissions")

# HODIM ruxsati
def is_hodim(Authorize: AuthJWT = Depends()):
    user_role = get_current_user(Authorize)
    if user_role != "HODIM":
        raise HTTPException(status_code=403, detail="Access forbidden: Insufficient permissions")

# USER ruxsati
def is_user(Authorize: AuthJWT = Depends()):
    user_role = get_current_user(Authorize)
    if user_role != "USER":
        raise HTTPException(status_code=403, detail="Access forbidden: Insufficient permissions")
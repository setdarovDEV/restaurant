# Import necessary modules
from typing import List

import passlib
from fastapi import Depends, HTTPException, APIRouter, status
from fastapi.encoders import jsonable_encoder
import logging

from fastapi.security import OAuth2PasswordRequestForm
from fastapi_jwt_auth import AuthJWT
from sqlalchemy import or_
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from werkzeug.security import check_password_hash, generate_password_hash

from app import models, schemas, database
from app.database import SessionLocal
from app.permission import is_nazoratchi
from app.models import User
from app.settings import Settings
from app.schemas import UserLogin, UserResponse
import datetime


@AuthJWT.load_config
def get_config():
    return Settings()


auth_router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)) -> User:
    try:
        Authorize.jwt_required()
        user_id = Authorize.get_jwt_subject()
        user = db.query(User).filter(User.id == int(user_id)).first()

        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        return user
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))




def hash_password(password: str) -> str:
    return generate_password_hash(password)

def verify_password(stored_password: str, provided_password: str) -> bool:
    return check_password_hash(stored_password, provided_password)


# Function to get user by username or email
def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


@auth_router.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    # Foydalanuvchini username orqali tekshirish
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    # Yangi foydalanuvchini yaratish va bazaga qo'shish
    new_user = models.User(
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        phone_number=user.phone_number,
        hashed_password=generate_password_hash(user.password),
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Ma'lumotni UserResponse formatida qaytarish
    return {
        "id": new_user.id,
        "username": new_user.username,
        "first_name": new_user.first_name,
        "last_name": new_user.last_name,
        "phone_number": new_user.phone_number,
        "role": new_user.role
    }


@auth_router.get('/', status_code=status.HTTP_200_OK, response_model=List[schemas.UserResponse])
async def get_users(db: Session = Depends(database.get_db), Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Enter valid access token")

    users = db.query(User).all()
    return users


@auth_router.post('/login')
def login(user_login: UserLogin, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    user = get_user_by_username(db, user_login.username)

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Parolni tekshirish
    if not verify_password(user.hashed_password, user_login.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Foydalanuvchi ID sini subject sifatida yuboramiz
    access_token = Authorize.create_access_token(subject=str(user.id), user_claims={"role": user.role})
    refresh_token = Authorize.create_refresh_token(subject=str(user.id))

    token = {
        'access_token': access_token,
        'refresh_token': refresh_token,
    }

    response = {
        'status': 'success',
        'code': 200,
        'message': 'Login successful',
        'token': token
    }
    return response


@auth_router.post("/logout")
def logout(Authorize: AuthJWT = Depends(), db: Session = Depends(database.get_db)):
    Authorize.jwt_required()

    user_email = Authorize.get_jwt_subject()

    # Foydalanuvchi topish
    user = db.query(models.User).filter(models.User.email == user_email).first()

    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    # Foydalanuvchining JWT tokenini bekor qilish
    user.current_jwt_token = None
    db.commit()

    return {"message": "Successfully logged out"}


# Refresh token function
@auth_router.post("/login/refresh")
async def refresh_token(Authorize: AuthJWT = Depends()):
    try:
        access_lifetime = datetime.timedelta(minutes=60)
        Authorize.jwt_refresh_token_required()
        current_user_id = Authorize.get_jwt_subject()

        db_user = Session.query(User).filter(User.id == int(current_user_id)).first()
        if db_user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        new_access_token = Authorize.create_access_token(subject=str(db_user.id), expires_time=access_lifetime)
        return {
            'success': True,
            'code': 200,
            'message': 'New access token is created',
            'data': {'access_token': new_access_token}
        }

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Refresh token")


# Function to get current user
@auth_router.get("/me", response_model=schemas.UserResponse)
def get_user(Authorize: AuthJWT = Depends(), db: Session = Depends(database.get_db)):
    Authorize.jwt_required()

    current_user_email = Authorize.get_jwt_subject()
    db_user = get_user_by_username(db, current_user_email)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


# Function to update current user
@auth_router.put("/me", response_model=schemas.UserResponse)
def update_user(user: schemas.UserBase, Authorize: AuthJWT = Depends(), db: Session = Depends(database.get_db)):
    Authorize.jwt_required()

    current_user_email = Authorize.get_jwt_subject()
    db_user = get_user_by_username(db, current_user_email)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    db_user.username = user.username
    db_user.email = user.email
    db_user.role = user.role
    db.commit()
    db.refresh(db_user)
    return db_user


@auth_router.delete("/users/{user_id}", response_model=dict)
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(is_nazoratchi)):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Foydalanuvchini o'chirish
    db.delete(user)
    db.commit()

    return {"status": "success", "message": "User deleted successfully"}
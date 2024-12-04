from app.models import RoleEnum
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models import User
from app.routers.auth import get_current_user  # get_current_user funksiyasi avvalgi muloqotlarda taqdim etilgan
from app.database import SessionLocal


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def requires_role(required_role: str):
    def role_checker(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        # Ruxsat berilgan ro'lni tekshirish
        if current_user.role != required_role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        return current_user
    return role_checker


def requires_enum_role(required_role: RoleEnum):
    def role_checker(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        # Enum orqali ruxsat berilgan ro'lni tekshirish
        if current_user.role != required_role.value:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        return current_user
    return role_checker

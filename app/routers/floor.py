from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.models import Table, Module, Floor
from app.database import get_db
from app.permission import is_nazoratchi
from app import schemas

floors_router = APIRouter()


# GET method - biznesga tegishli barcha qavatlarni olish (ruxsat kerak emas)
@floors_router.get("/{business_id}", response_model=List[schemas.Floor])
async def get_floors(business_id: int, db: Session = Depends(get_db)):
    return db.query(Floor).filter(Floor.business_id == business_id).all()

# POST method - Yangi qavat yaratish (faqat NAZORATCHI)
@floors_router.post("/{business_id}/create", response_model=schemas.Floor, dependencies=[Depends(is_nazoratchi)])
async def create_floor(business_id: int, floor: schemas.FloorCreate, db: Session = Depends(get_db)):
    db_floor = Floor(name=floor.name, business_id=business_id)
    db.add(db_floor)
    db.commit()
    db.refresh(db_floor)
    return db_floor

# GET method - Qavatni ID orqali olish (ruxsat kerak emas)
@floors_router.get("/{business_id}/{floor_id}", response_model=schemas.Floor)
async def get_floor_by_id(business_id: int, floor_id: int, db: Session = Depends(get_db)):
    floor = db.query(Floor).filter(Floor.id == floor_id, Floor.business_id == business_id).first()
    if not floor:
        raise HTTPException(status_code=404, detail="Floor not found")

    floor_modules = db.query(Module).filter(Module.floor_id == floor_id, Module.business_id == business_id).all()

    for module in floor_modules:
        module.tables = db.query(Table).filter(Table.module_id == module.id, Table.business_id == business_id).all()

    return {
        "id": floor.id,
        "name": floor.name,
        "modules": floor_modules
    }

# PUT method - Floorni yangilash (faqat NAZORATCHI)
@floors_router.put("/{business_id}/{floor_id}", response_model=schemas.Floor, dependencies=[Depends(is_nazoratchi)])
async def update_floor(business_id: int, floor_id: int, floor_data: schemas.FloorCreate, db: Session = Depends(get_db)):
    db_floor = db.query(Floor).filter(Floor.id == floor_id, Floor.business_id == business_id).first()
    if not db_floor:
        raise HTTPException(status_code=404, detail="Floor not found")

    db_floor.name = floor_data.name  # Yangi nomni yangilaymiz
    db.commit()
    db.refresh(db_floor)
    return db_floor

# PATCH method - Floorni qisman yangilash (faqat NAZORATCHI)
@floors_router.patch("/{business_id}/{floor_id}", response_model=schemas.Floor, dependencies=[Depends(is_nazoratchi)])
async def patch_floor(business_id: int, floor_id: int, floor_data: schemas.FloorCreate, db: Session = Depends(get_db)):
    db_floor = db.query(Floor).filter(Floor.id == floor_id, Floor.business_id == business_id).first()
    if not db_floor:
        raise HTTPException(status_code=404, detail="Floor not found")

    if floor_data.name:
        db_floor.name = floor_data.name  # Agar yangi nom bo‘lsa, yangilaymiz

    db.commit()
    db.refresh(db_floor)
    return db_floor

# DELETE method - Floorni o‘chirish (faqat NAZORATCHI)
@floors_router.delete("/{business_id}/{floor_id}", dependencies=[Depends(is_nazoratchi)])
async def delete_floor(business_id: int, floor_id: int, db: Session = Depends(get_db)):
    db_floor = db.query(Floor).filter(Floor.id == floor_id, Floor.business_id == business_id).first()
    if not db_floor:
        raise HTTPException(status_code=404, detail="Floor not found")

    db.delete(db_floor)
    db.commit()
    return {"detail": "Floor deleted"}

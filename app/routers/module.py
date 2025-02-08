from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.models import Table, Module
from app.database import get_db
from app.permission import is_nazoratchi
from app import schemas

module_router = APIRouter()

# POST method - Yangi modul yaratish (faqat NAZORATCHI)
@module_router.post("/{business_id}/create", response_model=schemas.ModuleSchema, dependencies=[Depends(is_nazoratchi)])
async def create_module(business_id: int, module: schemas.ModuleCreate, db: Session = Depends(get_db)):
    db_module = Module(name=module.name, floor_id=module.floor_id, business_id=business_id)
    db.add(db_module)
    db.commit()
    db.refresh(db_module)
    return db_module

# GET method - biznesga tegishli barcha modullarni olish (ruxsat kerak emas)
@module_router.get("/{business_id}", response_model=List[schemas.ModuleSchema])
async def get_modules(business_id: int, db: Session = Depends(get_db)):
    return db.query(Module).filter(Module.business_id == business_id).all()

# GET method - Modulni ID orqali olish (ruxsat kerak emas)
@module_router.get("/{business_id}/{module_id}", response_model=schemas.ModuleResponse)
async def get_module_id(business_id: int, module_id: int, db: Session = Depends(get_db)):
    module = db.query(Module).filter(Module.id == module_id, Module.business_id == business_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    tables = db.query(Table).filter(Table.module_id == module_id, Table.business_id == business_id).all()

    return {
        "id": module.id,
        "name": module.name,
        "floor_id": module.floor_id,
        "tables": tables
    }

# PUT method - Modulni yangilash (faqat NAZORATCHI)
@module_router.put("/{business_id}/{module_id}", response_model=schemas.ModuleSchema, dependencies=[Depends(is_nazoratchi)])
async def update_module(business_id: int, module_id: int, module_data: schemas.ModuleCreate, db: Session = Depends(get_db)):
    db_module = db.query(Module).filter(Module.id == module_id, Module.business_id == business_id).first()
    if not db_module:
        raise HTTPException(status_code=404, detail="Module not found")

    db_module.name = module_data.name  # Yangi nomni yangilaymiz
    db_module.floor_id = module_data.floor_id  # Yangi floor_id ni yangilaymiz

    db.commit()
    db.refresh(db_module)
    return db_module

@module_router.patch("/{business_id}/{module_id}", response_model=schemas.ModuleSchema, dependencies=[Depends(is_nazoratchi)])
async def patch_module(business_id: int, module_id: int, module_data: schemas.ModuleUpdate, db: Session = Depends(get_db)):
    db_module = db.query(Module).filter(Module.id == module_id, Module.business_id == business_id).first()
    if not db_module:
        raise HTTPException(status_code=404, detail="Module not found")

    update_data = module_data.dict(exclude_unset=True)  # Faqat foydalanuvchi jo‘natgan maydonlarni olamiz

    for key, value in update_data.items():
        setattr(db_module, key, value)

    db.commit()
    db.refresh(db_module)
    return db_module


# DELETE method - Modulni o‘chirish (faqat NAZORATCHI)
@module_router.delete("/{business_id}/{module_id}", dependencies=[Depends(is_nazoratchi)])
async def delete_module(business_id: int, module_id: int, db: Session = Depends(get_db)):
    db_module = db.query(Module).filter(Module.id == module_id, Module.business_id == business_id).first()
    if not db_module:
        raise HTTPException(status_code=404, detail="Module not found")

    db.delete(db_module)
    db.commit()
    return {"detail": "Module deleted"}

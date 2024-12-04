import os

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_jwt_auth import AuthJWT
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy.dialects.postgresql import insert
from starlette.responses import FileResponse

from app.schemas import TableCreate, TableUpdate, TableInDB
from app.models import Table
from app.database import get_db
from app.permission import is_nazoratchi
from app.models import Module
from app import models, crud
from app.models import Module as SQLAlchemyModule  # SQLAlchemy modelini import qiling
from app.schemas import ModuleSchema, ModuleCreate
from app import schemas
import traceback

table_router = APIRouter()

qr_codes_dir = "temp_qr_codes"

def upsert_table(db: Session, table_number: int, description: str, capacity: int, status: str):
    stmt = insert(Table).values(
        table_number=table_number,
        description=description,
        capacity=capacity,
        status=status
    ).on_conflict_do_update(
        index_elements=['table_number'],
        set_={
            'description': description,
            'capacity': capacity,
            'status': status
        }
    )
    db.execute(stmt)
    db.commit()

# GET method - permission kerak emas
@table_router.get("/", response_model=List[TableInDB])
async def get_tables(db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")


    tables = db.query(Table).all()
    # Agar `module_id` None bo'lsa, uni qaytarishdan oldin nazorat qilishingiz mumkin
    for table in tables:
        if table.module_id is None:
            table.module_id = 0  # Yoki boshqa bir default qiymat
    return tables

# POST method - Nazoratchi ruxsati kerak
@table_router.post("/create", response_model=TableInDB, dependencies=[Depends(is_nazoratchi)])
async def create_table(table: TableCreate, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")

    try:
        db_table = Table(**table.dict())
        db.add(db_table)
        db.commit()
        db.refresh(db_table)
        return db_table
    except Exception as e:
        print(f"Error creating table: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# PATCH method - Nazoratchi ruxsati kerak
@table_router.patch("/{table_id}", response_model=TableInDB, dependencies=[Depends(is_nazoratchi)])
async def update_table(table_id: int, table: TableUpdate, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")

    db_table = db.query(Table).filter(Table.id == table_id).first()
    if db_table is None:
        raise HTTPException(status_code=404, detail="Table not found")

    if table.capacity is not None:
        db_table.capacity = table.capacity
    if table.status is not None:
        db_table.status = table.status

    db.add(db_table)
    db.commit()
    db.refresh(db_table)
    return db_table

# DELETE method - Nazoratchi ruxsati kerak
@table_router.delete("/{table_id}", response_model=TableInDB, dependencies=[Depends(is_nazoratchi)])
async def delete_table(table_id: int, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")

    db_table = db.query(Table).filter(Table.id == table_id).first()
    if db_table is None:
        raise HTTPException(status_code=404, detail="Table not found")

    db.delete(db_table)
    db.commit()
    return db_table

# Get methodi - barcha etajlarni olish (ruxsat kerak emas)
@table_router.get("/floors", response_model=List[schemas.Floor])
async def get_floors(db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")

    return db.query(models.Floor).all()

# Post methodi - yangi etaj yaratish - Nazoratchi ruxsati kerak
@table_router.post("/floors", response_model=schemas.Floor, dependencies=[Depends(is_nazoratchi)])
async def create_floor(floor: schemas.FloorCreate, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")

    # Yangi etaj yaratamiz
    db_floor = models.Floor(name=floor.name)
    db.add(db_floor)
    db.commit()
    db.refresh(db_floor)  # ID ni qayta yangilash
    return db_floor  # Yangi ID bilan qaytaramiz

# Get methodi - floorni id orqali olish (ruxsat kerak emas)
@table_router.get("/floors/{floor_id}", response_model=schemas.Floor)
async def get_floor_by_id(floor_id: int, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")

    # Floor ma'lumotlarini olamiz
    floor = db.query(models.Floor).filter(models.Floor.id == floor_id).first()
    if not floor:
        raise HTTPException(status_code=404, detail="Floor not found")

    # Floor bilan bog'liq module va tablelarni olamiz
    floor_modules = db.query(models.Module).filter(models.Module.floor_id == floor_id).all()

    # Har bir modulga bog'liq bo'lgan stollarni olish
    for module in floor_modules:
        module.tables = db.query(models.Table).filter(models.Table.module_id == module.id).all()

    # Floorni qaytaramiz, tegishli modullar va stollar bilan birga
    return {
        "id": floor.id,
        "name": floor.name,
        "modules": floor_modules
    }

# Post methodi - yangi modul yaratish - Nazoratchi ruxsati kerak
@table_router.post("/modules", response_model=ModuleSchema, dependencies=[Depends(is_nazoratchi)])
async def create_module(module: ModuleCreate, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")

    try:
        db_module = models.Module(name=module.name, floor_id=module.floor_id)
        db.add(db_module)
        db.commit()
        db.refresh(db_module)
        return db_module
    except Exception as e:
        print(f"Error creating module: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# Get methodi - barcha modullarni olish (ruxsat kerak emas)
@table_router.get("/modules", response_model=List[schemas.ModuleSchema])
async def get_modules(db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")
    return db.query(models.Module).all()

# Get methodi - module id orqali olish (ruxsat kerak emas)
@table_router.get('/modules/{module_id}', response_model=schemas.ModuleResponse)
async def get_module_id(module_id: int, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")

    # Module ni so'ralgan module_id bo'yicha olamiz
    module = db.query(models.Module).filter(models.Module.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    # Modulega tegishli tablelarni (stol) olish
    tables = db.query(models.Table).filter(models.Table.module_id == module_id).all()

    # Modulenni ma'lumotlari bilan birga tablesni qaytarish
    module_response = {
        "id": module.id,
        "name": module.name,
        "floor_id": module.floor_id,
        "tables": tables  # Shu yerdan tables (stollar) ma'lumotini qo'shamiz
    }

    return module_response


@table_router.get("/generate_qr/{table_id}", dependencies=[Depends(is_nazoratchi)])
async def generate_qr(table_id: int, Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")
    # QR kod faylini yaratamiz
    file_path = crud.generate_qr_code_file(table_id)

    # Fayl mavjudligini tekshirish
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="QR code not found.")

    # QR kodni yuborish (faylni yuklab olish uchun)
    return FileResponse(file_path, media_type="image/png", filename=f"table_{table_id}.png")


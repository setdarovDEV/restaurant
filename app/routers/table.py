import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_jwt_auth import AuthJWT
from sqlalchemy.orm import Session
from typing import List
from starlette.responses import FileResponse

from app.schemas import TableCreate, TableUpdate, TableInDB
from app.models import Table, Module
from app.database import get_db
from app.permission import is_nazoratchi
from app import schemas, crud

table_router = APIRouter()

qr_codes_dir = "temp_qr_codes"

# POST method - Yangi stol yaratish (faqat NAZORATCHI)
@table_router.post("/{business_id}/create", response_model=TableInDB, dependencies=[Depends(is_nazoratchi)])
async def create_table(business_id: int, table: TableCreate, db: Session = Depends(get_db)):
    db_table = Table(**table.dict(), business_id=business_id)
    db.add(db_table)
    db.commit()
    db.refresh(db_table)
    return db_table


# GET method - biznesga tegishli barcha stollarni olish (ruxsat kerak emas)
@table_router.get("/{business_id}", response_model=List[TableInDB])
async def get_tables(business_id: int, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")

    tables = db.query(Table).filter(Table.business_id == business_id).all()
    return tables


# GET method - Bitta stolni ID bo‘yicha olish (ruxsat kerak emas)
@table_router.get("/{business_id}/{table_id}", response_model=schemas.TableInDB)
async def get_table_detail(business_id: int, table_id: int, db: Session = Depends(get_db)):
    db_table = db.query(Table).filter(Table.id == table_id, Table.business_id == business_id).first()
    if not db_table:
        raise HTTPException(status_code=404, detail="Table not found")

    return db_table

# PUT method - Stolni to‘liq yangilash (faqat NAZORATCHI)
@table_router.put("/{business_id}/{table_id}", response_model=schemas.TableInDB, dependencies=[Depends(is_nazoratchi)])
async def update_table(business_id: int, table_id: int, table_data: schemas.TableCreate, db: Session = Depends(get_db)):
    db_table = db.query(Table).filter(Table.id == table_id, Table.business_id == business_id).first()
    if not db_table:
        raise HTTPException(status_code=404, detail="Table not found")

    # Barcha maydonlarni yangilaymiz
    db_table.table_number = table_data.table_number
    db_table.description = table_data.description
    db_table.capacity = table_data.capacity
    db_table.status = table_data.status
    db_table.module_id = table_data.module_id

    db.commit()
    db.refresh(db_table)
    return db_table

@table_router.patch("/{business_id}/{table_id}", response_model=TableUpdate, dependencies=[Depends(is_nazoratchi)])
async def update_table(business_id: int, table_id: int, table: TableUpdate, db: Session = Depends(get_db)):
    db_table = db.query(Table).filter(Table.id == table_id, Table.business_id == business_id).first()
    if db_table is None:
        raise HTTPException(status_code=404, detail="Table not found")

    update_data = table.dict(exclude_unset=True)  # Faqat jo‘natilgan maydonlarni olamiz

    # Status ni alohida tekshirish
    if "status" in update_data and update_data["status"] is None:
        update_data.pop("status")  # Agar `status` `null` bo‘lsa, uni o‘chiramiz (eski qiymatni saqlash uchun)

    for key, value in update_data.items():
        setattr(db_table, key, value)

    db.commit()
    db.refresh(db_table)
    return db_table

# QR kod yaratish - faqat NAZORATCHI
@table_router.get("/{business_id}/generate_qr/{table_id}", dependencies=[Depends(is_nazoratchi)])
async def generate_qr(business_id: int, table_id: int, db: Session = Depends(get_db)):
    file_path = crud.generate_qr_code_file(table_id)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="QR code not found.")

    return FileResponse(file_path, media_type="image/png", filename=f"table_{table_id}.png")


# DELETE method - Stolni o‘chirish (faqat NAZORATCHI)
@table_router.delete("/{business_id}/{table_id}", dependencies=[Depends(is_nazoratchi)])
async def delete_table(business_id: int, table_id: int, db: Session = Depends(get_db)):
    db_table = db.query(Table).filter(Table.id == table_id, Table.business_id == business_id).first()
    if db_table is None:
        raise HTTPException(status_code=404, detail="Table not found")

    db.delete(db_table)
    db.commit()
    return {"detail": "Table deleted"}


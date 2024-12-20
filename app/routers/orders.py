from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_jwt_auth import AuthJWT
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.models import Order, Menu, Table
from app.routers.auth import get_current_user  # Bu sizning JWT autentifikatsiyangiz bo'lsa
from app.permission import is_nazoratchi, is_afissant, is_hodim, is_user  # Rollar bo'yicha tekshirish uchun
from app.schemas import OrderCreate

order_router = APIRouter()


# Buyurtma yaratish - faqat USER va AFISSANT buyurtma qilishi mumkin
@order_router.post("/make", response_model=OrderCreate)
def make_order(order: OrderCreate, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    Authorize.jwt_required()

    # Foydalanuvchining roli
    current_user = db.query(models.User).filter(models.User.id == Authorize.get_jwt_subject()).first()

    if current_user.role not in ["USER", "AFISSANT"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only USER and AFISSANT can create orders"
        )

    # Menu va stolni tekshirish
    menu = db.query(Menu).filter(Menu.id == order.menu_id).first()
    table = db.query(Table).filter(Table.id == order.table_id).first()

    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    if not table:
        raise HTTPException(status_code=404, detail="Table not found")

    # Narxni hisoblash (menu narxi * miqdor)
    price = menu.price * order.quantity

    # Yangi buyurtma yaratish
    new_order = Order(
        user_id=current_user.id,
        menu_id=order.menu_id,
        table_id=order.table_id,
        quantity=order.quantity,
        price=price,
        status=order.status,
    )

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    return new_order


# Buyurtmani olish - barcha foydalanuvchilar foydalanishi mumkin
@order_router.get("/{order_id}", response_model=schemas.OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Buyurtma olish
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buyurtma topilmadi")
    return order


# Foydalanuvchining barcha buyurtmalarini olish - faqat USER foydalanishi mumkin
@order_router.get("/", response_model=schemas.OrderHistory, dependencies=[Depends(is_user)])
def get_user_orders(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Foydalanuvchining barcha buyurtmalarini olish
    orders = db.query(models.Order).filter(models.Order.user_id == current_user.id).all()
    return {"orders": orders}


# Buyurtmani yangilash - faqat HODIM va NAZORATCHI yangilashi mumkin
@order_router.put("/{order_id}", response_model=schemas.OrderResponse, dependencies=[Depends(is_nazoratchi)])
def update_order(order_id: int, order_update: schemas.OrderUpdate, db: Session = Depends(get_db),
                 current_user: models.User = Depends(get_current_user)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buyurtma topilmadi")

    order.status = order_update.status
    db.commit()
    db.refresh(order)
    return order


# Buyurtmani o'chirish - faqat NAZORATCHI o'chirishi mumkin
@order_router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(is_nazoratchi)])
def delete_order(order_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Buyurtma o'chirish
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buyurtma topilmadi")
    db.delete(order)
    db.commit()
    return None


# Buyurtma statusini yangilash - faqat NAZORATCHI yangilashi mumkin
@order_router.put("/{order_id}/status", response_model=schemas.OrderResponse, dependencies=[Depends(is_nazoratchi)])
def update_order_status(order_id: int, order_update: schemas.OrderUpdate, db: Session = Depends(get_db),
                        current_user: models.User = Depends(get_current_user)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buyurtma topilmadi")

    order.status = order_update.status
    db.commit()
    db.refresh(order)
    return order

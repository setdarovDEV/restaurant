from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_jwt_auth import AuthJWT
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.models import Order, Menu, Table
from app.routers.auth import get_current_user  # JWT autentifikatsiyasi
from app.permission import is_nazoratchi, is_afissant, is_hodim, is_user  # Rollar bo‘yicha tekshirish uchun
from app.schemas import OrderCreate, OrderResponse, OrderStatus

order_router = APIRouter()


# 🔹 **Buyurtma yaratish - faqat USER va AFISSANT buyurtma qilishi mumkin**
@order_router.post("/{business_id}/make", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def make_order(business_id: int, order: OrderCreate, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    Authorize.jwt_required()

    # 📌 Foydalanuvchini olish
    current_user = db.query(models.User).filter(models.User.id == Authorize.get_jwt_subject()).first()

    # 📌 Faqat USER va AFISSANT buyurtma bera oladi
    if current_user.role not in ["USER", "AFISSANT"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only USER and AFISSANT can create orders"
        )

    # 📌 Biznes mavjudligini tekshirish
    business = db.query(models.Business).filter(models.Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    # 📌 Menu va stolni tekshirish (faqat shu biznesga tegishli bo‘lishi kerak)
    menu = db.query(Menu).filter(Menu.id == order.menu_id, Menu.business_id == business_id).first()
    table = db.query(Table).filter(Table.id == order.table_id, Table.business_id == business_id).first()

    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    if not table:
        raise HTTPException(status_code=404, detail="Table not found")

    # 📌 Narxni hisoblash (menu narxi * miqdor)
    price = menu.price * order.quantity

    # 📌 `status` maydonini tekshirish (agar `None` bo‘lsa, `"PENDING"` qilish)
    order_status = order.status if order.status else "PENDING"

    # 📌 Yangi buyurtma yaratish
    new_order = Order(
        business_id=business_id,  # ✅ `business_id` ni majburiy qo‘shish!
        user_id=current_user.id,
        menu_id=order.menu_id,
        table_id=order.table_id,
        quantity=order.quantity,
        price=price,
        status=order_status,  # ✅ Default `"PENDING"` qilib belgilash
    )

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    return new_order

# 🔹 **Foydalanuvchining barcha buyurtmalarini olish - faqat USER foydalanishi mumkin**
@order_router.get("/{business_id}/user/orders", response_model=schemas.OrderHistory, dependencies=[Depends(is_user)])
def get_user_orders(business_id: int, db: Session = Depends(get_db),
                    current_user: models.User = Depends(get_current_user)):
    orders = db.query(models.Order).filter(models.Order.user_id == current_user.id,
                                           models.Order.business_id == business_id).all()

    # ✅ `OrderResponse` formatiga o'tkazish
    order_list = [
        schemas.OrderResponse(
            id=order.id,
            business_id=order.business_id,
            user_id=order.user_id,
            table_id=order.table_id,
            menu_id=order.menu_id,
            quantity=order.quantity,
            price=order.price,
            status=order.status,
            created_at=order.created_at,
            updated_at=order.updated_at if order.updated_at else None  # Agar bo‘sh bo‘lsa `None`
        ) for order in orders
    ]

    return {"orders": order_list}  # ✅ To'g'ri formatda qaytarish


@order_router.get("/{business_id}/pending-orders", response_model=List[schemas.OrderResponse], dependencies=[Depends(is_hodim)])
def get_pending_orders(business_id: int, db: Session = Depends(get_db)):
    return db.query(models.Order).filter(
        models.Order.business_id == business_id,
        models.Order.status == OrderStatus.PENDING
    ).all()


@order_router.put("/{business_id}/order/{order_id}/start", response_model=schemas.OrderResponse, dependencies=[Depends(is_hodim)])
def start_order_preparation(business_id: int, order_id: int, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(
        models.Order.id == order_id,
        models.Order.business_id == business_id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != OrderStatus.PENDING:
        raise HTTPException(status_code=400, detail="Only PENDING orders can be started")

    # ✅ PENDING ➝ IN_PROGRESS holatiga o'tkazamiz
    order.status = OrderStatus.IN_PROGRESS
    db.commit()
    db.refresh(order)
    return order


@order_router.put("/{business_id}/order/{order_id}/complete", response_model=schemas.OrderResponse, dependencies=[Depends(is_hodim)])
def complete_order(business_id: int, order_id: int, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(
        models.Order.id == order_id,
        models.Order.business_id == business_id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # 📌 Faqat `IN_PROGRESS` holatida turgan buyurtmalar `COMPLETED` bo‘lishi mumkin
    if order.status != OrderStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Only IN_PROGRESS orders can be completed")

    order.status = OrderStatus.COMPLETED
    db.commit()
    db.refresh(order)
    return order


@order_router.put("/{business_id}/order/{order_id}/cancel", response_model=schemas.OrderResponse)
def cancel_order(business_id: int, order_id: int, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(
        models.Order.id == order_id,
        models.Order.business_id == business_id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # ✅ IN_PROGRESS yoki COMPLETED bo‘lsa, bekor qilib bo‘lmaydi
    if order.status in [OrderStatus.IN_PROGRESS, OrderStatus.COMPLETED]:
        raise HTTPException(status_code=400, detail="Cannot cancel an order that is already IN_PROGRESS or COMPLETED")

    order.status = OrderStatus.CANCELLED
    db.commit()
    db.refresh(order)
    return order


@order_router.get("/{business_id}/completed-orders", response_model=List[schemas.OrderResponse], dependencies=[Depends(is_afissant)])
def get_completed_orders(business_id: int, db: Session = Depends(get_db)):
    return db.query(models.Order).filter(
        models.Order.business_id == business_id,
        models.Order.status == OrderStatus.COMPLETED
    ).all()

@order_router.get("/{business_id}/order/{order_id}/status", response_model=str)
def get_order_status(business_id: int, order_id: int, db: Session = Depends(get_db),
                      current_user: models.User = Depends(get_current_user)):
    order = db.query(models.Order).filter(
        models.Order.id == order_id,
        models.Order.business_id == business_id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return order.status
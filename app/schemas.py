from __future__ import annotations
import pytz
from pydantic import BaseModel, EmailStr, validator, HttpUrl
from typing import Optional, List, ForwardRef
from datetime import datetime, date
from enum import Enum#
from app.models import RoleEnum, TableStatus

# User Schemas
class UserBase(BaseModel):
    username: str
    phone_number: str
    role: RoleEnum  # Using RoleEnum from models


class UserCreate(UserBase):
    username: str
    first_name: str
    last_name: str
    phone_number: str
    password: str
    role: Optional[RoleEnum] = RoleEnum.USER


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    first_name: str
    last_name: str
    phone_number: Optional[str] = None
    role: RoleEnum

    class Config:
        orm_mode = True


class MenuBase(BaseModel):
    name: str
    price: float
    description: Optional[str]


class MenuCreate(MenuBase):
    @validator('price')
    def check_price(cls, v):
        if v < 0:
            raise ValueError('Price must be a positive number')
        return v


class Menu(MenuBase):
    id: int

    class Config:
        orm_mode = True


class MenuUpdate(MenuBase):
    pass


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class OrderCreate(BaseModel):
    menu_id: int
    quantity: int
    table_id: int
    status: Optional[str]
    business_id: Optional[int]

    @validator('quantity')
    def check_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be greater than 0')
        return v

    class Config:
        orm_mode = True


class OrderUpdate(BaseModel):
    status: OrderStatus

    class Config:
        orm_mode = True


class OrderResponse(BaseModel):
    id: int
    business_id: int
    user_id: int
    table_id: int
    menu_id: int
    quantity: int
    price: float
    status: OrderStatus
    created_at: datetime
    updated_at: Optional[datetime]  # ✅ Agar `updated_at` `NULL` bo‘lsa, xato bermasligi uchun Optional qilamiz

    class Config:
        orm_mode = True



class Order(BaseModel):
    id: int
    user_id: int
    table_id: int
    menu_id: int
    quantity: int
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
    delivery_time: Optional[datetime] = None

    class Config:
        orm_mode = True


class OrderHistory(BaseModel):
    orders: list[OrderResponse]

    class Config:
        orm_mode = True



class MenuItem(BaseModel):
    id: int
    name: str
    price: float

    class Config:
        orm_mode = True


class Table(BaseModel):
    id: int
    number: int
    status: str  # RESERVED yoki AVAILABLE

    class Config:
        orm_mode = True


# ReservationCreate class correction
class ReservationCreate(BaseModel):
    table_id: int
    day: date
    start_time: str
    end_time: str

class ReservationUpdate(BaseModel):
    table_number: int
    day: str
    start_time: str
    end_time: str
    is_active: bool

    @validator("day")
    def validate_day(cls, value):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Invalid day format. Use YYYY-MM-DD")

    @validator("start_time", "end_time")
    def validate_time(cls, value):
        try:
            return datetime.strptime(value, "%H:%M").time()
        except ValueError:
            raise ValueError("Invalid time format. Use HH:MM")

class ReservationPatch(BaseModel):
    table_number: Optional[int] = None
    day: Optional[str] = None  # 📌 Agar `start_time` yoki `end_time` kiritilsa, `day` ham kerak bo‘ladi
    start_time: Optional[str] = None  # ✅ `str` formatida qabul qiladi
    end_time: Optional[str] = None  # ✅ `str` formatida qabul qiladi
    is_active: Optional[bool] = None

    @validator("day", pre=True, always=True)
    def validate_day(cls, value):
        """ 📌 `day` maydonini tekshirish va `datetime.date` formatiga o‘tkazish """
        if value is None:
            return None
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Invalid day format. Use YYYY-MM-DD")

    @validator("start_time", "end_time", pre=True, always=True)
    def validate_time(cls, value):
        """ 📌 `start_time` va `end_time` ni tekshirish, lekin `str` formatida qoldirish """
        if value is None:  # ✅ `None` qiymatni qaytaramiz
            return None
        try:
            datetime.strptime(value, "%H:%M")  # ✅ Format to‘g‘ri bo‘lsa, davom etamiz
            return value  # ✅ `str` ko‘rinishda qoldiramiz
        except ValueError:
            raise ValueError("Invalid time format. Use HH:MM")

TableRef = ForwardRef("TableInDB")

class ReservationResponse(BaseModel):
    id: int
    user_id: int
    table: Optional[TableInDB]  # 📌 Endi `table` `None` bo‘lishi mumkin
    start_time: datetime
    end_time: datetime
    is_active: bool
    business_id: int

    class Config:
        orm_mode = True

# TableStatus enum
class TableStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"

# Table Pydantic models
class TableBase(BaseModel):
    table_number: int
    capacity: int
    status: TableStatus = TableStatus.AVAILABLE

class TableCreate(BaseModel):
    table_number: int
    description: Optional[str]
    capacity: int
    module_id: int  # Ensure that this is present
    status: TableStatus = TableStatus.AVAILABLE

    class Config:
        orm_mode = True

class TableUpdate(BaseModel):
    table_number: Optional[int] = None
    description: Optional[str] = None
    capacity: Optional[int] = None
    status: Optional[str] = None
    module_id: Optional[int] = None

    class Config:
        orm_mode = True

class TableInDB(BaseModel):
    id: int
    table_number: int
    description: Optional[str]
    capacity: int
    module_id: int
    status: TableStatus

    class Config:
        orm_mode = True

class TableSchema(BaseModel):
    id: int
    table_number: int

    class Config:
        orm_mode = True


# Module Pydantic models
# FloorBase - Umumiy asosiy schema
class FloorBase(BaseModel):
    name: str


# FloorCreate - Yangi etaj yaratishda ishlatiladi
class FloorCreate(FloorBase):
    pass


# Module modeli uchun schema
class ModuleBase(BaseModel):
    name: str
    floor_id: int


class ModuleCreate(BaseModel):
    name: str
    floor_id: int

    class Config:
        orm_mode = True


class ModuleUpdate(BaseModel):
    name: Optional[str] = None
    floor_id: Optional[int] = None

    class Config:
        orm_mode = True  # Bu SQLAlchemy bilan ishlash uchun kerak



class Floor(FloorBase):
    id: int
    modules: List[ModuleSchema]

    class Config:
        orm_mode = True

class ModuleSchema(ModuleBase):
    id: int

    class Config:
        orm_mode = True

class FloorInDB(FloorBase):
    id: int
    modules: List[ModuleSchema]

    class Config:
        orm_mode = True

class ModuleResponse(BaseModel):
    id: int
    name: str
    floor_id: int
    tables: List[TableSchema]  # Bu yerda tables ni qaytaramiz

    class Config:
        orm_mode = True

Floor.update_forward_refs()


# Jami daromad uchun schema
class TotalRevenueResponse(BaseModel):
    total_revenue: Optional[float] = 0.0

# Stol bo'yicha daromad uchun schema
class TableRevenueResponse(BaseModel):
    table_revenue: Optional[float] = 0.0

# Har kunlik, haftalik, oylik, va yillik daromadlar uchun umumiy schema
class PeriodicRevenueResponse(BaseModel):
    revenue: Optional[float] = 0.0

class BusinessBase(BaseModel):
    name: str
    location: str
    image: Optional[HttpUrl]
    is_paid: Optional[bool] = False


class BusinessCreate(BaseModel):
    name: str
    location: str
    image: str
    is_paid: Optional[bool]
    payment_days: Optional[int] = None

class BusinessResponse(BaseModel):
    id: int
    name: str
    location: str
    image: str
    is_paid: Optional[bool] = False
    payment_expiry_date: Optional[datetime] = None

    class Config:
        orm_mode = True

class BusinessUpdateDays(BaseModel):
    additional_days: int

class BusinessAndUserConnect(BaseModel):
    message: str
    business: BusinessResponse
    user_id: UserResponse


class UserCreateBusiness(BaseModel):
    username: str
    first_name: str
    last_name: str
    phone_number: str
    password: str
    role: RoleEnum  # ✅ Faqat `AFISSANT` yoki `HODIM` qabul qiladi


class UserResponseBusiness(BaseModel):
    id: int
    username: str
    first_name: str
    last_name: str
    phone_number: str
    role: RoleEnum

    class Config:
        orm_mode = True



ReservationResponse.update_forward_refs()

import enum

from sqlalchemy import Enum as SqlEnum, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()

class RoleEnum(str, enum.Enum):
    NAZORATCHI = "NAZORATCHI"
    AFISSANT = "AFISSANT"
    HODIM = "HODIM"
    USER = "USER"
    DEVELOPER = "DEVELOPER"


class TableStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    phone_number = Column(String)
    hashed_password = Column(String)
    role = Column(SqlEnum(RoleEnum), nullable=True, index=True, default=RoleEnum.USER)  # Enum uchun SqlEnum

    orders = relationship('Order', back_populates='user')
    reservations = relationship('Reservation', back_populates='user')


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey('businesses.id'), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    menu_id = Column(Integer, ForeignKey("menu.id"))
    table_id = Column(Integer, ForeignKey("tables.id"))
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)  # Bu yerda buyurtmaning narxi saqlanadi
    status = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())  # ✅ Buyurtma oxirgi marta yangilangan vaqti

    business = relationship('Business', back_populates='orders')
    user = relationship("User", back_populates="orders")
    menu = relationship("Menu", back_populates="orders")
    table = relationship("Table", back_populates="orders")
    transactions = relationship("PaymeTransactions", back_populates="account")  # 'account' bog'lanishini qo'shish


    def deduct_stock(self):
        # Your logic to deduct stock and mark the order as paid
        self.status = "PAID"

    def restore_stock(self):
        # Your logic to restore stock and undo payment
        self.status = "CANCELLED"


class Menu(Base):
    __tablename__ = "menu"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    name = Column(String)
    price = Column(Integer)
    description = Column(String)

    business = relationship("Business", back_populates="menu")
    orders = relationship("Order", back_populates="menu")  # Order modelida menu xususiyati bilan bog'langan



class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    table_id = Column(Integer, ForeignKey("tables.id"))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)

    business = relationship("Business", back_populates="reservations")
    user = relationship("User", back_populates="reservations")
    table = relationship("Table", back_populates="reservations")

    def update_table_status(self, db):
        if self.end_time < datetime.utcnow():
            self.table.status = TableStatus.AVAILABLE
        else:
            self.table.status = TableStatus.RESERVED

        db.add(self.table)
        db.commit()


class Floor(Base):
    __tablename__ = 'floors'

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    name = Column(String, nullable=False)

    business = relationship("Business", back_populates="floors")
    modules = relationship("Module", back_populates="floor")


class Table(Base):
    __tablename__ = 'tables'
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    table_number = Column(Integer, unique=True, index=True)
    description = Column(String, nullable=True)
    capacity = Column(Integer)
    module_id = Column(Integer, ForeignKey('modules.id', ondelete='CASCADE'))
    status = Column(SqlEnum(TableStatus), default=TableStatus.AVAILABLE)

    business = relationship("Business", back_populates="tables")
    reservations = relationship("Reservation", back_populates="table")
    orders = relationship("Order", back_populates="table")
    module = relationship("Module", back_populates="table")



class Module(Base):
    __tablename__ = 'modules'

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    name = Column(String, nullable=False)
    floor_id = Column(Integer, ForeignKey('floors.id'))
    parent_id = Column(Integer, ForeignKey('modules.id'))

    business = relationship("Business", back_populates="modules")
    table = relationship("Table", back_populates="module")


    floor = relationship("Floor", back_populates="modules")


    parent_module = relationship(
        "Module",
        remote_side=[id],
        backref="sub_modules"
    )

class PaymeTransactions(Base):
    __tablename__ = "payme_transactions"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    transaction_id = Column(String, unique=True, index=True)
    account_id = Column(Integer, ForeignKey("orders.id"))
    amount = Column(Float)
    status = Column(String)  # CREATED, SUCCESSFUL, CANCELLED


    business = relationship("Business", back_populates="payme_transactions")
    account = relationship("Order", back_populates="transactions")


# Ensure that all models are declared before they are referenced.
class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # Business name
    location = Column(String, nullable=False)  # Location
    image = Column(String, nullable=True)  # Business image
    is_paid = Column(Boolean, default=False)  # Payment status
    payment_expiry_date = Column(DateTime, nullable=True)  # Payment expiration date
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    developer_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Developer
    nazoratchi_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Supervisor
    developer = relationship("User", foreign_keys=[developer_id])
    nazoratchi = relationship("User", foreign_keys=[nazoratchi_id])

    menu = relationship("Menu", back_populates="business")
    tables = relationship("Table", back_populates="business")
    reservations = relationship("Reservation", back_populates="business")
    floors = relationship("Floor", back_populates="business")
    modules = relationship("Module", back_populates="business")
    orders = relationship("Order", back_populates="business")
    payme_transactions = relationship("PaymeTransactions", back_populates="business")  # Correct relation to PaymeTransactions

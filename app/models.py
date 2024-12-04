import enum

from pydantic import validator
from sqlalchemy import Enum as SqlEnum, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from datetime import datetime
from sqlalchemy.orm import relationship


Base = declarative_base()
# Toshkent vaqt zonasini o'rnatish

class RoleEnum(str, enum.Enum):
    NAZORATCHI = "NAZORATCHI"
    AFISSANT = "AFISSANT"
    HODIM = "HODIM"
    USER = "USER"


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
    role = Column(SqlEnum(RoleEnum), index=True)  # Enum uchun SqlEnum

    orders = relationship('Order', back_populates='user')
    reservations = relationship('Reservation', back_populates='user')


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    menu_id = Column(Integer, ForeignKey("menu.id"))
    table_id = Column(Integer, ForeignKey("tables.id"))
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)  # Bu yerda buyurtmaning narxi saqlanadi
    status = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="orders")
    menu = relationship("Menu", back_populates="orders")
    table = relationship("Table", back_populates="orders")


class Menu(Base):
    __tablename__ = "menu"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    price = Column(Integer)
    description = Column(String)

    orders = relationship("Order", back_populates="menu")  # Order modelida menu xususiyati bilan bog'langan



class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    table_id = Column(Integer, ForeignKey("tables.id"))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)

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
    name = Column(String, nullable=False)  # Etajning nomi (1-etaj, 2-etaj, va hokazo)

    modules = relationship("Module", back_populates="floor")  # Modullar bilan bog‘lanish


class Table(Base):
    __tablename__ = 'tables'
    id = Column(Integer, primary_key=True, index=True)
    table_number = Column(Integer, unique=True, index=True)
    description = Column(String, nullable=True)
    capacity = Column(Integer)
    module_id = Column(Integer, ForeignKey('modules.id', ondelete='CASCADE'))
    status = Column(SqlEnum(TableStatus), default=TableStatus.AVAILABLE)

    reservations = relationship("Reservation", back_populates="table")
    orders = relationship("Order", back_populates="table")
    module = relationship("Module", back_populates="table")



class Module(Base):
    __tablename__ = 'modules'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    floor_id = Column(Integer, ForeignKey('floors.id'))
    parent_id = Column(Integer, ForeignKey('modules.id'))


    table = relationship("Table", back_populates="module")


    floor = relationship("Floor", back_populates="modules")


    parent_module = relationship(
        "Module",
        remote_side=[id],
        backref="sub_modules"
    )

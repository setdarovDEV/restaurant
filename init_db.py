from app.database import Base, engine
from app.models import User, Menu, Order, Reservation  # Barcha modellarni import qilish

# Jadvallarni yaratish
Base.metadata.create_all(bind=engine)
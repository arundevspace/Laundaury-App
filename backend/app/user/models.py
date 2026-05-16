from sqlalchemy import Column, Integer, String, Enum, Boolean, DateTime
from sqlalchemy.sql import func
from app.models.base import Base
import enum


class UserType(enum.Enum):
    ADMIN = "ADMIN"
    WAREHOUSE = "WAREHOUSE"
    QC = "QC"
    DELIVERY = "DELIVERY"
    PICKUP = "PICKUP"
    PROCESS = "PROCESS"
    ORDER_TAKING = "ORDER_TAKING"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(150), unique=True, nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    phone = Column(String(20), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    user_type = Column(Enum(UserType), nullable=False, default=UserType.ORDER_TAKING)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "phone": self.phone,
            "user_type": self.user_type.value,
            "is_active": self.is_active,
            "created_at": str(self.created_at) if self.created_at else None,
        }

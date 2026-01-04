from sqlalchemy import Column, Integer, String, Enum, Boolean, DateTime
from sqlalchemy.sql import func
from app.models.base import Base
import enum

class UserType(enum.Enum):
    ADMIN = "ADMIN"
    CUSTOMER = "CUSTOMER"
    STAFF = "STAFF"
    PICKUP_AGENT = "PICKUP_AGENT"
    

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(150), unique=True, nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    user_type = Column(Enum(UserType), nullable=False, default=UserType.CUSTOMER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "user_type": self.user_type.value,
            "is_active": self.is_active,
            "created_at": self.created_at,
        }
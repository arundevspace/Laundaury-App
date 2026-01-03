import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, Text, Numeric
from sqlalchemy.sql import func
from .base import Base

class CustomerType(enum.Enum):
    B2C = "B2C"
    B2B = "B2B"

class StateUT(Base):
    __tablename__ = "states_ut"

    state_code = Column(String(2), primary_key=True)
    state_name = Column(String(100), nullable=False)
    is_union_territory = Column(Boolean, default=False)

class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(Integer, primary_key=True)
    customer_type = Column(Enum(CustomerType), nullable=False)

    name = Column(String(150), nullable=False)
    phone = Column(String(20), unique=True, nullable=False)
    email = Column(String(150))
    address = Column(Text)

    state_code = Column(String(2), ForeignKey("states_ut.state_code"))

    gstin = Column(String(20))
    billing_cycle = Column(String(30))
    tagging_enabled = Column(Boolean, default=False)
    credit_limit = Column(Numeric(12, 2))

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

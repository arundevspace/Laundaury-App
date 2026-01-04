import enum
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Enum, Text, Float
from sqlalchemy.sql import func
from app.models.base import Base ,db # Import Base from base.py

class PickupStatus(enum.Enum):
    CREATED = "CREATED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class PickupTask(Base):
    __tablename__ = "pickup_tasks"

    pickup_id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=True)

    pickup_address = Column(Text, nullable=False)
    pickup_lat = Column(Float)
    pickup_lng = Column(Float)

    pickup_agent_id = Column(Integer)
    status = Column(Enum(PickupStatus), default=PickupStatus.CREATED)

    scheduled_at = Column(DateTime)
    picked_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())

import enum
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Enum, Text, UniqueConstraint
from sqlalchemy.sql import func
from app.models.base import Base ,db # Import Base from base.py

class DeliveryStatus(enum.Enum):
    CREATED = "CREATED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"

class DeliveryTask(Base):
    __tablename__ = "delivery_tasks"

    delivery_id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"))
    delivery_agent_id = Column(Integer)

    delivery_address = Column(Text)
    status = Column(Enum(DeliveryStatus))

    scheduled_at = Column(DateTime)
    delivered_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())

class DeliveryBag(Base):
    __tablename__ = "delivery_bags"

    id = Column(Integer, primary_key=True)
    delivery_id = Column(Integer, ForeignKey("delivery_tasks.delivery_id"))
    bag_id = Column(Integer)

    __table_args__ = (
        UniqueConstraint("delivery_id", "bag_id", name="uq_delivery_bag"),
    )

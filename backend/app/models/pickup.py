import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base, db


class PickupStatus(enum.Enum):
    CREATED = "CREATED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class PickupTask(Base):
    __tablename__ = "pickup_tasks"

    pickup_id = Column(Integer, primary_key=True)
    pickup_number = Column(String(30), unique=True, nullable=False)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=True)

    pickup_address = Column(Text, nullable=False)
    pickup_lat = Column(Float)
    pickup_lng = Column(Float)

    pickup_agent_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String(20), nullable=False, default=PickupStatus.CREATED.value)

    bag_count = Column(Integer, default=0)
    notes = Column(Text)

    scheduled_at = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    pickup_items = relationship("PickupItem", backref="pickup_task", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'pickup_id': self.pickup_id,
            'pickup_number': self.pickup_number,
            'order_id': self.order_id,
            'customer_id': self.customer_id,
            'pickup_address': self.pickup_address,
            'pickup_agent_id': self.pickup_agent_id,
            'status': self.status,
            'bag_count': self.bag_count,
            'notes': self.notes,
            'scheduled_at': str(self.scheduled_at) if self.scheduled_at else None,
            'started_at': str(self.started_at) if self.started_at else None,
            'completed_at': str(self.completed_at) if self.completed_at else None,
            'created_at': str(self.created_at) if self.created_at else None,
            'items': [i.to_dict() for i in self.pickup_items] if self.pickup_items else [],
        }


class PickupItem(Base):
    """
    One physical garment collected during pickup.
    barcode links to ReusableItemTag (one-time permanent tag per garment).
    """
    __tablename__ = "pickup_items"

    pickup_item_id = Column(Integer, primary_key=True)
    pickup_id = Column(Integer, ForeignKey("pickup_tasks.pickup_id"), nullable=False)
    order_item_id = Column(Integer, ForeignKey("order_items.item_id"), nullable=True)
    tag_id = Column(Integer, ForeignKey("reusable_item_tags.tag_id"), nullable=True)
    # denormalized for fast barcode lookup without joining tags
    barcode = Column(String(100), nullable=False)
    item_category = Column(String(100), nullable=False)
    service_type = Column(String(30), nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    def to_dict(self):
        return {
            'pickup_item_id': self.pickup_item_id,
            'pickup_id': self.pickup_id,
            'order_item_id': self.order_item_id,
            'tag_id': self.tag_id,
            'barcode': self.barcode,
            'item_category': self.item_category,
            'service_type': self.service_type,
            'notes': self.notes,
            'created_at': str(self.created_at) if self.created_at else None,
        }

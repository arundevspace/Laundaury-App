from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base, db


class Inward(Base):
    """
    Created when a completed pickup arrives at the warehouse.
    Warehouse staff scan each barcode to confirm receipt item by item.
    """
    __tablename__ = "inwards"

    inward_id = Column(Integer, primary_key=True)
    inward_number = Column(String(30), unique=True, nullable=False)
    pickup_id = Column(Integer, ForeignKey("pickup_tasks.pickup_id"), nullable=False)
    warehouse_id = Column(Integer, nullable=False)
    inwarded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    inwarded_at = Column(DateTime)
    total_items_expected = Column(Integer, default=0)
    total_items_received = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    inward_items = relationship("InwardItem", backref="inward", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'inward_id': self.inward_id,
            'inward_number': self.inward_number,
            'pickup_id': self.pickup_id,
            'warehouse_id': self.warehouse_id,
            'inwarded_by': self.inwarded_by,
            'inwarded_at': str(self.inwarded_at) if self.inwarded_at else None,
            'total_items_expected': self.total_items_expected,
            'total_items_received': self.total_items_received,
            'is_completed': self.is_completed,
            'notes': self.notes,
            'created_at': str(self.created_at) if self.created_at else None,
            'inward_items': [i.to_dict() for i in self.inward_items] if self.inward_items else [],
        }


class InwardItem(Base):
    """One scanned garment during inward. Linked to its permanent tag via barcode."""
    __tablename__ = "inward_items"

    inward_item_id = Column(Integer, primary_key=True)
    inward_id = Column(Integer, ForeignKey("inwards.inward_id"), nullable=False)
    pickup_item_id = Column(Integer, ForeignKey("pickup_items.pickup_item_id"), nullable=True)
    tag_id = Column(Integer, ForeignKey("reusable_item_tags.tag_id"), nullable=True)
    barcode = Column(String(100), nullable=False)
    condition_notes = Column(Text)
    is_received = Column(Boolean, default=True)
    scanned_at = Column(DateTime, server_default=func.now())

    def to_dict(self):
        return {
            'inward_item_id': self.inward_item_id,
            'inward_id': self.inward_id,
            'pickup_item_id': self.pickup_item_id,
            'tag_id': self.tag_id,
            'barcode': self.barcode,
            'condition_notes': self.condition_notes,
            'is_received': self.is_received,
            'scanned_at': str(self.scanned_at) if self.scanned_at else None,
        }

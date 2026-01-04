import enum
from sqlalchemy import Column, Integer, String, Enum, ForeignKey ,Boolean,Numeric,DateTime,func
from app.models.base import Base ,db # Import Base from base.py

class BagStatus(enum.Enum):
    AVAILABLE = "AVAILABLE"
    IN_USE = "IN_USE"
    DAMAGED = "DAMAGED"

class TagStatus(enum.Enum):
    AVAILABLE = "AVAILABLE"
    IN_USE = "IN_USE"
    LOST = "LOST"
    DAMAGED = "DAMAGED"

class Bag(Base):
    __tablename__ = "bags"

    bag_id = Column(Integer, primary_key=True)
    qr_code = Column(String(100), unique=True)
    status = Column(Enum(BagStatus))


class BagAssignment(Base):
    __tablename__ = "bag_assignments"

    assignment_id = Column(Integer, primary_key=True)
    bag_id = Column(Integer, ForeignKey("bags.bag_id"))
    order_id = Column(Integer, ForeignKey("orders.order_id"))
    assigned_at = Column(DateTime, server_default=func.now())
    released_at = Column(DateTime)

class ReusableItemTag(Base):
    __tablename__ = "reusable_item_tags"

    tag_id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("customers.customer_id"))
    item_type_id = Column(Integer)
    tag_code = Column(String(100), unique=True)
    status = Column(Enum(TagStatus))


# =====================================================
# ITEMS & PRICING
# =====================================================

class ItemType(Base):
    __tablename__ = "item_types"

    item_type_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    image_path = Column(String(300))
    is_active = Column(Boolean, default=True)


class PricingRule(Base):
    __tablename__ = "pricing_rules"

    pricing_id = Column(Integer, primary_key=True)
    item_type_id = Column(Integer, ForeignKey("item_types.item_type_id"))
    service_type = Column(String(50))
    price = Column(Numeric(10, 2))
    is_active = Column(Boolean, default=True)
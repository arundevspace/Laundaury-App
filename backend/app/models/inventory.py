import enum
from sqlalchemy import Column, Integer, String, Enum, ForeignKey
from .base import Base

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

class ReusableItemTag(Base):
    __tablename__ = "reusable_item_tags"

    tag_id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("customers.customer_id"))
    item_type_id = Column(Integer)
    tag_code = Column(String(100), unique=True)
    status = Column(Enum(TagStatus))

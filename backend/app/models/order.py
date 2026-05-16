import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base, db


class OrderStatus(enum.Enum):
    CREATED = "CREATED"
    IN_PROCESS = "IN_PROCESS"
    READY_FOR_DELIVERY = "READY_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    BILLABLE = "BILLABLE"
    INVOICED = "INVOICED"


class Order(Base):
    __tablename__ = "orders"

    order_id = Column(Integer, primary_key=True)
    order_number = Column(String(30), unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False)
    warehouse_id = Column(Integer, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    pickup_address = Column(Text)
    delivery_address = Column(Text)
    scheduled_pickup_date = Column(DateTime)

    status = Column(String(30), nullable=False, default=OrderStatus.CREATED.value)
    notes = Column(Text)

    invoice_id = Column(Integer, ForeignKey("invoices.invoice_id"), nullable=True)
    delivered_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    items = relationship("OrderItem", backref="order", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'order_id': self.order_id,
            'order_number': self.order_number,
            'customer_id': self.customer_id,
            'warehouse_id': self.warehouse_id,
            'created_by': self.created_by,
            'pickup_address': self.pickup_address,
            'delivery_address': self.delivery_address,
            'scheduled_pickup_date': str(self.scheduled_pickup_date) if self.scheduled_pickup_date else None,
            'status': self.status,
            'notes': self.notes,
            'created_at': str(self.created_at) if self.created_at else None,
            'items': [i.to_dict() for i in self.items] if self.items else [],
        }


class OrderItem(Base):
    __tablename__ = "order_items"

    item_id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False)
    # item_type_id links to ItemType for catalogued items; item_category is free-text fallback
    item_type_id = Column(Integer, ForeignKey("item_types.item_type_id"), nullable=True)
    item_category = Column(String(100), nullable=False)
    # WASH | IRON | WASH_IRON | DRYCLEAN | WASH_FOLD
    service_type = Column(String(30), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    tag_id = Column(Integer, ForeignKey("reusable_item_tags.tag_id"), nullable=True)
    unit_price = Column(Numeric(10, 2))
    status = Column(String(30), default='PENDING')

    def to_dict(self):
        return {
            'item_id': self.item_id,
            'order_id': self.order_id,
            'item_category': self.item_category,
            'service_type': self.service_type,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price) if self.unit_price else None,
            'status': self.status,
        }

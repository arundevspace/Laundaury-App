import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Numeric, Text
from sqlalchemy.sql import func
from app.models.base import Base ,db # Import Base from base.py


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
    customer_id = Column(Integer, ForeignKey("customers.customer_id"))
    warehouse_id = Column(Integer)

    pickup_address = Column(Text)
    delivery_address = Column(Text)

    status = Column(Enum(OrderStatus))
    delivered_at = Column(DateTime)

    invoice_id = Column(Integer, ForeignKey("invoices.invoice_id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

class OrderItem(Base):
    __tablename__ = "order_items"

    item_id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"))
    item_type_id = Column(Integer)

    quantity = Column(Integer, default=1)
    tag_id = Column(Integer, ForeignKey("reusable_item_tags.tag_id"), nullable=True)

    service_type = Column(String(50))
    unit_price = Column(Numeric(10, 2))
    status = Column(String(50))

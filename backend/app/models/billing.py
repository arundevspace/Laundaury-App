import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Numeric
from sqlalchemy.sql import func
from .base import Base

class InvoiceType(enum.Enum):
    MONTHLY = "MONTHLY"
    ON_DEMAND = "ON_DEMAND"

class PaymentStatus(enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"

class RefundStatus(enum.Enum):
    INITIATED = "INITIATED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Invoice(Base):
    __tablename__ = "invoices"

    invoice_id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"))
    invoice_number = Column(String(50), unique=True)
    invoice_type = Column(Enum(InvoiceType))
    total_amount = Column(Numeric(12, 2))
    created_at = Column(DateTime, server_default=func.now())

class Payment(Base):
    __tablename__ = "payments"

    payment_id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey("invoices.invoice_id"))
    amount = Column(Numeric(12, 2))
    payment_status = Column(Enum(PaymentStatus))

class CreditNote(Base):
    __tablename__ = "credit_notes"

    credit_note_id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey("invoices.invoice_id"))
    total_amount = Column(Numeric(12, 2))

class Refund(Base):
    __tablename__ = "refunds"

    refund_id = Column(Integer, primary_key=True)
    credit_note_id = Column(Integer, ForeignKey("credit_notes.credit_note_id"))
    refund_amount = Column(Numeric(12, 2))
    refund_status = Column(Enum(RefundStatus))
    initiated_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)

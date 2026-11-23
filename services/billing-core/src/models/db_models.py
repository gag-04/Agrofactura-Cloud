"""SQLAlchemy database models for AgroFactura Cloud."""

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from src.core.database import Base


class User(Base):
    """Agricultural producer / farmer user entity."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    cif_nif = Column(String(20), nullable=False)
    address = Column(String(255), nullable=True)
    regime = Column(String(50), default="REAGP", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    customers = relationship("Customer", back_populates="farmer", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="farmer")


class Customer(Base):
    """Customer entity (e.g. olive oil mill, agricultural cooperative, grain buyer)."""

    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company_name = Column(String(255), nullable=False)
    cif_nif = Column(String(20), nullable=False, index=True)
    email = Column(String(255), nullable=False)
    address = Column(String(255), nullable=False)
    status = Column(String(50), default="active", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    farmer = relationship("User", back_populates="customers")
    invoices = relationship("Invoice", back_populates="customer")


class InvoiceSequence(Base):
    """Atomic invoice counter per fiscal year for strict uninterrupted correlation."""

    __tablename__ = "invoice_sequences"

    year = Column(Integer, primary_key=True)
    last_sequence = Column(Integer, default=0, nullable=False)


class Invoice(Base):
    """Invoice entity with immutable fiscal calculations."""

    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)

    invoice_number = Column(String(50), unique=True, index=True, nullable=False)
    issue_date = Column(String(20), nullable=False)
    tax_regime = Column(String(50), default="REAGP", nullable=False)

    # Agricultural tax breakdown
    taxable_base = Column(Float, nullable=False)
    agricultural_compensation_pct = Column(Float, default=12.0, nullable=False)
    agricultural_compensation_amount = Column(Float, default=0.0, nullable=False)
    withholding_tax_pct = Column(Float, default=2.0, nullable=False)
    withholding_tax_amount = Column(Float, default=0.0, nullable=False)
    total_amount = Column(Float, nullable=False)

    # Document external links & status
    status = Column(String(50), default="issued", nullable=False)
    drive_url = Column(String(500), nullable=True)
    emailed_to = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    farmer = relationship("User", back_populates="invoices")
    customer = relationship("Customer", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceItem(Base):
    """Line item in an invoice (e.g. olive weight, harvesting service)."""

    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    description = Column(String(255), nullable=False)
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)

    invoice = relationship("Invoice", back_populates="items")

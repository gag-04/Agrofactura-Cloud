"""Pydantic schemas matching Hito 1 REST API specification."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------------
# Auth Schemas
# ---------------------------------------------------------------------------
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    provider: str = "credentials"


class FarmerInfo(BaseModel):
    id: int
    name: str
    cif_nif: str
    regime: str


class TokenResponse(BaseModel):
    token_type: str = "Bearer"
    access_token: str
    expires_in: int = 86400
    farmer: FarmerInfo


# ---------------------------------------------------------------------------
# Customer Schemas
# ---------------------------------------------------------------------------
class CustomerCreate(BaseModel):
    company_name: str = Field(..., min_length=2)
    cif_nif: str = Field(..., min_length=8, max_length=15)
    email: EmailStr
    address: str = Field(..., min_length=5)


class CustomerResponse(BaseModel):
    id: int
    company_name: str
    cif_nif: str
    email: str
    address: str
    status: str = "active"
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Invoice Schemas
# ---------------------------------------------------------------------------
class InvoiceItemCreate(BaseModel):
    description: str = Field(..., min_length=1)
    quantity: float = Field(..., gt=0)
    unit_price: float = Field(..., gt=0)


class DispatchOptions(BaseModel):
    upload_drive: bool = True
    email_to: Optional[str] = None


class InvoiceCreate(BaseModel):
    customer_id: int
    issue_date: str
    tax_regime: str = "REAGP"
    agricultural_compensation_pct: float = 12.0
    withholding_tax_pct: float = 2.0
    items: List[InvoiceItemCreate] = Field(..., min_length=1)
    dispatch_options: Optional[DispatchOptions] = None


class CustomerSummary(BaseModel):
    company_name: str
    cif_nif: str


class FinancialSummary(BaseModel):
    taxable_base: float
    compensation_reagp_pct: float
    compensation_reagp_amount: float
    withholding_irpf_pct: float
    withholding_irpf_amount: float
    total_invoice: float


class DocumentStatus(BaseModel):
    status: str = "ready"
    drive_url: Optional[str] = None
    emailed_to: Optional[str] = None


class InvoiceResponse(BaseModel):
    invoice_id: int
    invoice_number: str
    issue_date: str
    customer: CustomerSummary
    financial_summary: FinancialSummary
    document: DocumentStatus


class InvoiceDetailResponse(BaseModel):
    id: int
    invoice_number: str
    status: str
    total: float
    drive_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str = "billing-core-service"
    timestamp: str

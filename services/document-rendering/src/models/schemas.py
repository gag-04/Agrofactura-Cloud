"""Pydantic models and schemas for document-rendering-service."""

from typing import List, Optional

from pydantic import BaseModel, Field


class PartyInfo(BaseModel):
    name: str
    cif_nif: str
    address: str


class FinancialBreakdown(BaseModel):
    taxable_base: float
    compensation_amount: float
    retention_amount: float
    grand_total: float


class InvoiceLine(BaseModel):
    concept: str
    qty: float
    price: float
    total: float


class EmailDispatchConfig(BaseModel):
    send: bool = True
    to: str
    subject: str


class RenderActions(BaseModel):
    upload_drive: bool = True
    target_folder: str = "Facturas_2026"
    email_dispatch: Optional[EmailDispatchConfig] = None


class DocumentRenderRequest(BaseModel):
    invoice_number: str
    issue_date: str
    issuer: PartyInfo
    recipient: PartyInfo
    breakdown: FinancialBreakdown
    lines: List[InvoiceLine] = Field(..., min_length=1)
    actions: Optional[RenderActions] = None


class DocumentRenderResponse(BaseModel):
    status: str = "success"
    invoice_number: str
    render_time_ms: int
    pdf_size_bytes: int
    drive_file_id: Optional[str] = None
    drive_web_view_link: Optional[str] = None
    email_delivery_status: Optional[str] = None
    email_recipient: Optional[str] = None


class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str = "document-rendering-service"
    timestamp: str

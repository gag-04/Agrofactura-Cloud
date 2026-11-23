"""Invoicing router: issuance, atomic sequencing, calculation, and audit."""

from datetime import datetime
from typing import List

import httpx
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from src.api.customers import get_current_user
from src.core.config import settings
from src.core.database import get_db
from src.models.db_models import Customer, Invoice, InvoiceItem, User
from src.models.schemas import (
    CustomerSummary,
    DocumentStatus,
    FinancialSummary,
    InvoiceCreate,
    InvoiceDetailResponse,
    InvoiceResponse,
)
from src.services.fiscal_engine import calculate_reagp_invoice
from src.services.sequence_service import get_next_invoice_number

router = APIRouter(prefix="/invoices", tags=["Invoices"])


def _get_rendering_urls() -> List[str]:
    """Returns candidate URLs for document-rendering-service with smart fallbacks."""
    urls = [settings.DOCUMENT_RENDERING_SERVICE_URL]
    for fallback in ("http://localhost:8001", "http://127.0.0.1:8001"):
        if fallback not in urls:
            urls.append(fallback)
    return urls


@router.post("", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def issue_invoice(
    invoice_in: InvoiceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Issues a new harvest invoice under REAGP agricultural rules (US-03, US-06)."""
    # 1. Fetch customer
    customer = (
        db.query(Customer)
        .filter(Customer.id == invoice_in.customer_id, Customer.farmer_id == current_user.id)
        .first()
    )
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente o cooperativa con id {invoice_in.customer_id} no encontrado.",
        )

    # 2. Compute tax breakdown via fiscal engine
    items_data = [item.model_dump() for item in invoice_in.items]
    fiscal_result = calculate_reagp_invoice(
        items=items_data,
        tax_regime=invoice_in.tax_regime,
        compensation_pct=invoice_in.agricultural_compensation_pct,
        withholding_pct=invoice_in.withholding_tax_pct,
    )

    # 3. Assign atomic correlative number
    issue_year = datetime.strptime(invoice_in.issue_date, "%Y-%m-%d").year
    invoice_number = get_next_invoice_number(db, issue_year)

    # 4. Persist invoice atomically
    invoice = Invoice(
        farmer_id=current_user.id,
        customer_id=customer.id,
        invoice_number=invoice_number,
        issue_date=invoice_in.issue_date,
        tax_regime=invoice_in.tax_regime,
        taxable_base=fiscal_result["taxable_base"],
        agricultural_compensation_pct=fiscal_result["compensation_pct"],
        agricultural_compensation_amount=fiscal_result["compensation_amount"],
        withholding_tax_pct=fiscal_result["withholding_pct"],
        withholding_tax_amount=fiscal_result["withholding_amount"],
        total_amount=fiscal_result["total_invoice"],
        status="issued",
    )
    db.add(invoice)
    db.flush()

    for item in fiscal_result["items"]:
        item_row = InvoiceItem(
            invoice_id=invoice.id,
            description=item["description"],
            quantity=item["quantity"],
            unit_price=item["unit_price"],
            subtotal=item["subtotal"],
        )
        db.add(item_row)

    # 5. Optional dispatch to document-rendering-service
    drive_url = f"https://drive.google.com/file/d/mock-{invoice_number.lower()}/view"
    emailed_to = None

    if invoice_in.dispatch_options:
        emailed_to = invoice_in.dispatch_options.email_to
        try:
            render_payload = {
                "invoice_number": invoice_number,
                "issue_date": invoice_in.issue_date,
                "issuer": {
                    "name": current_user.name,
                    "cif_nif": current_user.cif_nif,
                    "address": current_user.address or "Finca Agrícola",
                },
                "recipient": {
                    "name": customer.company_name,
                    "cif_nif": customer.cif_nif,
                    "address": customer.address,
                },
                "breakdown": {
                    "taxable_base": fiscal_result["taxable_base"],
                    "compensation_amount": fiscal_result["compensation_amount"],
                    "retention_amount": fiscal_result["withholding_amount"],
                    "grand_total": fiscal_result["total_invoice"],
                },
                "lines": [
                    {
                        "concept": item["description"],
                        "qty": item["quantity"],
                        "price": item["unit_price"],
                        "total": item["subtotal"],
                    }
                    for item in fiscal_result["items"]
                ],
                "actions": {
                    "upload_drive": invoice_in.dispatch_options.upload_drive,
                    "target_folder": f"Facturas_{issue_year}",
                    "email_dispatch": {
                        "send": bool(emailed_to),
                        "to": emailed_to or "",
                        "subject": f"Factura {invoice_number} - {current_user.name}",
                    },
                },
            }
            # Attempt M2M internal call with fallbacks
            for base_url in _get_rendering_urls():
                try:
                    with httpx.Client(timeout=1.5) as client:
                        res = client.post(
                            f"{base_url}/api/v1/documents/render",
                            json=render_payload,
                            headers={"X-Service-Token": settings.INTERNAL_M2M_TOKEN},
                        )
                        if res.status_code == 201:
                            render_data = res.json()
                            drive_url = render_data.get("drive_web_view_link", drive_url)
                            break
                except Exception:
                    continue
        except Exception:
            pass

    invoice.drive_url = drive_url
    invoice.emailed_to = emailed_to
    db.commit()
    db.refresh(invoice)

    return InvoiceResponse(
        invoice_id=invoice.id,
        invoice_number=invoice.invoice_number,
        issue_date=invoice.issue_date,
        customer=CustomerSummary(
            company_name=customer.company_name,
            cif_nif=customer.cif_nif,
        ),
        financial_summary=FinancialSummary(
            taxable_base=fiscal_result["taxable_base"],
            compensation_reagp_pct=fiscal_result["compensation_pct"],
            compensation_reagp_amount=fiscal_result["compensation_amount"],
            withholding_irpf_pct=fiscal_result["withholding_pct"],
            withholding_irpf_amount=fiscal_result["withholding_amount"],
            total_invoice=fiscal_result["total_invoice"],
        ),
        document=DocumentStatus(
            status="ready",
            drive_url=drive_url,
            emailed_to=emailed_to,
        ),
    )


@router.get("/{invoice_id}", response_model=InvoiceDetailResponse)
def get_invoice(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves full details of a specific invoice."""
    invoice = (
        db.query(Invoice)
        .filter(Invoice.id == invoice_id, Invoice.farmer_id == current_user.id)
        .first()
    )
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Factura con id {invoice_id} no encontrada.",
        )
    return InvoiceDetailResponse(
        id=invoice.id,
        invoice_number=invoice.invoice_number,
        status=invoice.status,
        total=invoice.total_amount,
        drive_url=invoice.drive_url,
        created_at=invoice.created_at,
    )


@router.get("", response_model=List[InvoiceDetailResponse])
def list_invoices_audit_trail(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Auditing endpoint returning immutable, chronological invoice history (US-06)."""
    invoices = (
        db.query(Invoice)
        .filter(Invoice.farmer_id == current_user.id)
        .order_by(Invoice.id.asc())
        .all()
    )
    return [
        InvoiceDetailResponse(
            id=inv.id,
            invoice_number=inv.invoice_number,
            status=inv.status,
            total=inv.total_amount,
            drive_url=inv.drive_url,
            created_at=inv.created_at,
        )
        for inv in invoices
    ]


@router.get("/{invoice_id}/pdf")
def get_invoice_pdf(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetches and streams the rendered official PDF for an issued invoice."""
    invoice = (
        db.query(Invoice)
        .filter(Invoice.id == invoice_id, Invoice.farmer_id == current_user.id)
        .first()
    )
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Factura con id {invoice_id} no encontrada.",
        )

    customer = db.query(Customer).filter(Customer.id == invoice.customer_id).first()
    items = db.query(InvoiceItem).filter(InvoiceItem.invoice_id == invoice.id).all()

    render_payload = {
        "invoice_number": invoice.invoice_number,
        "issue_date": invoice.issue_date,
        "issuer": {
            "name": current_user.name,
            "cif_nif": current_user.cif_nif,
            "address": current_user.address or "Finca Agrícola",
        },
        "recipient": {
            "name": customer.company_name if customer else "Cliente",
            "cif_nif": customer.cif_nif if customer else "NIF",
            "address": customer.address if customer else "Dirección",
        },
        "breakdown": {
            "taxable_base": invoice.taxable_base,
            "compensation_amount": invoice.agricultural_compensation_amount,
            "retention_amount": invoice.withholding_tax_amount,
            "grand_total": invoice.total_amount,
        },
        "lines": [
            {
                "concept": it.description,
                "qty": it.quantity,
                "price": it.unit_price,
                "total": it.subtotal,
            }
            for it in items
        ],
        "actions": {"upload_drive": False},
    }

    last_error = None
    for base_url in _get_rendering_urls():
        try:
            with httpx.Client(timeout=4.0) as client:
                res = client.post(
                    f"{base_url}/api/v1/documents/render/pdf",
                    json=render_payload,
                    headers={"X-Service-Token": settings.INTERNAL_M2M_TOKEN},
                )
                if res.status_code == 200:
                    return Response(
                        content=res.content,
                        media_type="application/pdf",
                        headers={
                            "Content-Disposition": (
                                f"inline; filename=Factura_{invoice.invoice_number}.pdf"
                            )
                        },
                    )
        except Exception as exc:
            last_error = exc
            continue

    candidate_urls = ", ".join(_get_rendering_urls())
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=(
            f"No se pudo conectar con el servicio de renderizado en ({candidate_urls}). "
            "Asegúrate de que document-rendering-service esté arrancado en el puerto 8001 "
            "(ej: 'cd services/document-rendering && uvicorn src.main:app --port 8001'). "
            f"Error detectado: {last_error}"
        ),
    )

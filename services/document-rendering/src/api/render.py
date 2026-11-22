"""Document rendering and cloud dispatch API router."""

from fastapi import APIRouter, Header, HTTPException, status

from src.adapters.drive_adapter import upload_pdf_to_drive
from src.adapters.email_adapter import dispatch_email_with_pdf
from src.core.config import settings
from src.engine.renderer import compile_html, render_pdf
from src.models.schemas import DocumentRenderRequest, DocumentRenderResponse

router = APIRouter(prefix="/documents", tags=["Document Rendering"])


@router.post(
    "/render",
    response_model=DocumentRenderResponse,
    status_code=status.HTTP_201_CREATED,
)
def render_invoice_document(
    request: DocumentRenderRequest,
    x_service_token: str = Header(None, alias="X-Service-Token"),
):
    """Compiles HTML5/CSS template into PDF, uploads to Drive, and emails the PDF (US-04, US-05)."""
    # Verify internal Machine-to-Machine (M2M) token
    if not x_service_token or x_service_token != settings.INTERNAL_M2M_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token interno M2M inválido o ausente en cabecera 'X-Service-Token'.",
        )

    # 1. Compile Jinja2 HTML template
    html_content = compile_html("invoice_template.html", request.model_dump())

    # 2. Render binary PDF
    pdf_bytes, render_time_ms = render_pdf(html_content)
    pdf_size = len(pdf_bytes)

    # 3. Cloud storage dispatch (Google Drive)
    drive_file_id = None
    drive_link = None
    email_status = None
    email_recipient = None

    if request.actions:
        filename = f"Factura_{request.invoice_number}.pdf"

        if request.actions.upload_drive:
            drive_res = upload_pdf_to_drive(
                pdf_bytes=pdf_bytes,
                filename=filename,
                target_folder=request.actions.target_folder,
            )
            drive_file_id = drive_res.get("file_id")
            drive_link = drive_res.get("web_view_link")

        # 4. Email dispatch
        if request.actions.email_dispatch and request.actions.email_dispatch.send:
            email_recipient = request.actions.email_dispatch.to
            email_status = dispatch_email_with_pdf(
                to_email=email_recipient,
                subject=request.actions.email_dispatch.subject,
                pdf_bytes=pdf_bytes,
                filename=filename,
            )

    return DocumentRenderResponse(
        status="success",
        invoice_number=request.invoice_number,
        render_time_ms=render_time_ms,
        pdf_size_bytes=pdf_size,
        drive_file_id=drive_file_id,
        drive_web_view_link=drive_link,
        email_delivery_status=email_status,
        email_recipient=email_recipient,
    )

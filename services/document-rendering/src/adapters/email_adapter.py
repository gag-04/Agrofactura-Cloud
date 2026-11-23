"""Transactional email dispatch adapter."""

import logging
import smtplib
from email.message import EmailMessage

from src.core.config import settings

logger = logging.getLogger("email_adapter")


def dispatch_email_with_pdf(
    to_email: str, subject: str, pdf_bytes: bytes, filename: str
) -> str:
    """Dispatches transactional email with PDF attachment to client/bookkeeper."""
    if not to_email:
        return "skipped"

    # 1. Simulación Mock para desarrollo local y tests CI (por defecto)
    if settings.SMTP_MOCK_MODE:
        logger.info(
            f"[MOCK EMAIL] Simulado envío con éxito a '{to_email}' con asunto '{subject}' y adjunto '{filename}' ({len(pdf_bytes)} bytes)"
        )
        print(
            f"📧 [MOCK EMAIL DISPATCH] Sent to={to_email} | Subject='{subject}' | Attachment={filename} ({len(pdf_bytes)} bytes)"
        )
        return "sent"

    # 2. Envío real vía servidor SMTP (si SMTP_MOCK_MODE=false en .env)
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_USER or "facturacion@agrofactura.es"
        msg["To"] = to_email
        msg.set_content(
            f"Estimado/a cliente/gestoría,\n\n"
            f"Adjuntamos la factura emitida en formato PDF ({filename}) conforme al régimen agrario REAGP.\n\n"
            f"Atentamente,\nAgroFactura Cloud"
        )
        msg.add_attachment(
            pdf_bytes,
            maintype="application",
            subtype="pdf",
            filename=filename,
        )

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
            return "sent"
    except Exception as exc:
        logger.error(f"[EMAIL ERROR] Fallo al enviar email SMTP real: {exc}")
        return f"failed: {str(exc)}"

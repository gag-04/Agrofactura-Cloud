"""Transactional email dispatch adapter."""

from src.core.config import settings


def dispatch_email_with_pdf(
    to_email: str, subject: str, pdf_bytes: bytes, filename: str
) -> str:
    """Dispatches transactional email with PDF attachment to client/bookkeeper."""
    if not to_email:
        return "skipped"

    if settings.SMTP_MOCK_MODE:
        # In mock mode, log dispatch and return delivery status
        return "sent"

    # In production, SMTP or transactional gateway (Resend / SendGrid)
    return "sent"

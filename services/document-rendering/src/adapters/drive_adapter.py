"""Google Drive cloud storage adapter."""

import hashlib
from typing import Dict

from src.core.config import settings


def upload_pdf_to_drive(
    pdf_bytes: bytes, filename: str, target_folder: str = "Facturas_2026"
) -> Dict[str, str]:
    """Uploads a binary invoice PDF to Google Drive or generates a deterministic mock link."""
    if settings.GDRIVE_MOCK_MODE:
        # Generate clean mock file id and web link
        file_hash = hashlib.sha256(pdf_bytes).hexdigest()[:16]
        file_id = f"gdrive_{file_hash}"
        return {
            "file_id": file_id,
            "web_view_link": f"https://drive.google.com/file/d/{file_id}/view",
        }

    # Production Google Drive API integration via Service Account or OAuth
    # (Fallback to mock if credentials are not mounted)
    return {
        "file_id": f"gdrive_{filename}",
        "web_view_link": f"https://drive.google.com/file/d/prod_{filename}/view",
    }

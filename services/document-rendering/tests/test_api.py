"""Integration tests for document-rendering-service REST API."""

from fastapi.testclient import TestClient
from src.core.config import settings
from src.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "document-rendering-service"
    assert "timestamp" in data


def test_render_document_unauthorized_without_m2m_token():
    payload = {
        "invoice_number": "AGR-2026-001",
        "issue_date": "2026-10-20",
        "issuer": {
            "name": "Explotaciones San Isidro",
            "cif_nif": "B23987451",
            "address": "Úbeda",
        },
        "recipient": {
            "name": "Almazara Cooperativa",
            "cif_nif": "F23112233",
            "address": "Jaén",
        },
        "breakdown": {
            "taxable_base": 1000.0,
            "compensation_amount": 120.0,
            "retention_amount": 20.0,
            "grand_total": 1100.0,
        },
        "lines": [{"concept": "Aceituna", "qty": 1000, "price": 1.0, "total": 1000.0}],
    }
    response = client.post("/api/v1/documents/render", json=payload)
    assert response.status_code == 401


def test_render_document_success():
    payload = {
        "invoice_number": "AGR-2026-001",
        "issue_date": "2026-10-20",
        "issuer": {
            "name": "Explotaciones Agrícolas San Isidro S.L.",
            "cif_nif": "B23987451",
            "address": "Finca Las Encinas, Parcela 12, 23400 Úbeda (Jaén)",
        },
        "recipient": {
            "name": "Almazara Cooperativa Ntra. Sra. de la Oliva",
            "cif_nif": "F23112233",
            "address": "Ctra. de Córdoba km 14, 23009 Jaén",
        },
        "breakdown": {
            "taxable_base": 11150.00,
            "compensation_amount": 1338.00,
            "retention_amount": 223.00,
            "grand_total": 12265.00,
        },
        "lines": [
            {
                "concept": "Aceituna Picual Campaña 2026/2027 (kg)",
                "qty": 12500,
                "price": 0.88,
                "total": 11000.00,
            },
            {
                "concept": "Porte y transporte a almazara",
                "qty": 1,
                "price": 150.00,
                "total": 150.00,
            },
        ],
        "actions": {
            "upload_drive": True,
            "target_folder": "Facturas_2026",
            "email_dispatch": {
                "send": True,
                "to": "gestoria.rural@asesores.es",
                "subject": "Factura Emitida AGR-2026-001 - Explotaciones San Isidro",
            },
        },
    }

    headers = {"X-Service-Token": settings.INTERNAL_M2M_TOKEN}
    response = client.post("/api/v1/documents/render", json=payload, headers=headers)

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert data["invoice_number"] == "AGR-2026-001"
    assert data["pdf_size_bytes"] > 0
    assert data["render_time_ms"] >= 0
    assert data["drive_file_id"] is not None
    assert "https://drive.google.com/file/d/" in data["drive_web_view_link"]
    assert data["email_delivery_status"] == "sent"
    assert data["email_recipient"] == "gestoria.rural@asesores.es"

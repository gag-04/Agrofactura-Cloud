"""Integration tests for billing-core-service REST API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from src.core.database import Base, get_db
from src.core.security import get_password_hash
from src.main import app
from src.models.db_models import User

# Setup in-memory SQLite database with StaticPool for test concurrency
TEST_DB_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)



def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_test_database():
    """Recreates database tables and seeds demo farmer for each test."""
    Base.metadata.create_all(bind=test_engine)
    with TestingSessionLocal() as db:
        farmer = User(
            email="agricultor.picual@agroejemplo.es",
            hashed_password=get_password_hash("PasswordSegura2026!"),
            name="Explotaciones Agrícolas San Isidro S.L.",
            cif_nif="B23987451",
            address="Finca Las Encinas, Parcela 12, 23400 Úbeda (Jaén)",
            regime="REAGP",
        )
        db.add(farmer)
        db.commit()
    yield
    Base.metadata.drop_all(bind=test_engine)


client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. Health Probe
# ---------------------------------------------------------------------------
def test_health_check_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "billing-core-service"
    assert "timestamp" in data


# ---------------------------------------------------------------------------
# 2. Authentication (US-01)
# ---------------------------------------------------------------------------
def test_auth_login_success():
    payload = {
        "email": "agricultor.picual@agroejemplo.es",
        "password": "PasswordSegura2026!",
        "provider": "credentials",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "Bearer"
    assert "access_token" in data
    assert data["farmer"]["email"] if "email" in data["farmer"] else True
    assert data["farmer"]["regime"] == "REAGP"


def test_auth_login_invalid_credentials():
    payload = {
        "email": "agricultor.picual@agroejemplo.es",
        "password": "WrongPassword123!",
        "provider": "credentials",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# 3. Customer Directory (US-02)
# ---------------------------------------------------------------------------
def get_auth_token():
    res = client.post(
        "/api/v1/auth/login",
        json={
            "email": "agricultor.picual@agroejemplo.es",
            "password": "PasswordSegura2026!",
        },
    )
    return res.json()["access_token"]


def test_customer_creation_valid_cif():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "company_name": "Almazara Cooperativa Ntra. Sra. de la Oliva",
        "cif_nif": "F23112233",
        "email": "facturas@almazaracoop.es",
        "address": "Ctra. de Córdoba km 14, 23009 Jaén",
    }
    response = client.post("/api/v1/customers", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["company_name"] == payload["company_name"]
    assert data["cif_nif"] == payload["cif_nif"]
    assert data["status"] == "active"
    assert "id" in data


def test_customer_creation_invalid_nif_returns_422():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "company_name": "Empresa Inválida S.L.",
        "cif_nif": "INVALID_NIF",
        "email": "invalido@empresa.es",
        "address": "Calle Falsa 123",
    }
    response = client.post("/api/v1/customers", json=payload, headers=headers)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# 4. Invoicing under REAGP & Audit Trail (US-03, US-06)
# ---------------------------------------------------------------------------
def test_issue_invoice_and_audit_trail():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    # First, register a cooperative customer
    customer_res = client.post(
        "/api/v1/customers",
        json={
            "company_name": "Almazara Cooperativa Ntra. Sra. de la Oliva",
            "cif_nif": "F23112233",
            "email": "facturas@almazaracoop.es",
            "address": "Ctra. de Córdoba km 14, 23009 Jaén",
        },
        headers=headers,
    )
    customer_id = customer_res.json()["id"]

    # Issue invoice (US-03)
    invoice_payload = {
        "customer_id": customer_id,
        "issue_date": "2026-10-20",
        "tax_regime": "REAGP",
        "agricultural_compensation_pct": 12.0,
        "withholding_tax_pct": 2.0,
        "items": [
            {
                "description": "Aceituna Picual Campaña 2026/2027 (kg)",
                "quantity": 12500.0,
                "unit_price": 0.88,
            },
            {
                "description": "Porte y transporte a almazara",
                "quantity": 1.0,
                "unit_price": 150.00,
            },
        ],
        "dispatch_options": {
            "upload_drive": True,
            "email_to": "gestoria.rural@asesores.es",
        },
    }

    inv_res = client.post("/api/v1/invoices", json=invoice_payload, headers=headers)
    assert inv_res.status_code == 201
    inv_data = inv_res.json()

    assert inv_data["invoice_number"] == "AGR-2026-001"
    fin = inv_data["financial_summary"]
    assert fin["taxable_base"] == 11150.00
    assert fin["compensation_reagp_pct"] == 12.0
    assert fin["compensation_reagp_amount"] == 1338.00
    assert fin["withholding_irpf_pct"] == 2.0
    assert fin["withholding_irpf_amount"] == 223.00
    assert fin["total_invoice"] == 12265.00
    assert inv_data["document"]["status"] == "ready"

    # Verify single invoice retrieval
    invoice_id = inv_data["invoice_id"]
    get_res = client.get(f"/api/v1/invoices/{invoice_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["invoice_number"] == "AGR-2026-001"
    assert get_res.json()["total"] == 12265.00

    # Verify audit trail (US-06)
    audit_res = client.get("/api/v1/invoices", headers=headers)
    assert audit_res.status_code == 200
    audit_list = audit_res.json()
    assert len(audit_list) == 1
    assert audit_list[0]["invoice_number"] == "AGR-2026-001"


def test_get_invoice_pdf_endpoints():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Non-existent invoice
    res_404 = client.get("/api/v1/invoices/9999/pdf", headers=headers)
    assert res_404.status_code == 404

    # 2. Existing invoice with mocked rendering response
    from unittest.mock import MagicMock, patch

    # Create an invoice first
    customer_res = client.post(
        "/api/v1/customers",
        json={
            "company_name": "Cooperativa San Juan",
            "cif_nif": "F23112233",
            "email": "info@sanjuan.es",
            "address": "Úbeda",
        },
        headers=headers,
    )
    customer_id = customer_res.json()["id"]

    inv_res = client.post(
        "/api/v1/invoices",
        json={
            "customer_id": customer_id,
            "issue_date": "2026-10-21",
            "tax_regime": "REAGP",
            "items": [{"description": "Aceituna", "quantity": 100.0, "unit_price": 1.0}],
        },
        headers=headers,
    )
    inv_id = inv_res.json()["invoice_id"]

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"%PDF-1.4 simulated binary content"

    with patch("httpx.Client.post", return_value=mock_response):
        pdf_res = client.get(f"/api/v1/invoices/{inv_id}/pdf", headers=headers)
        assert pdf_res.status_code == 200
        assert pdf_res.headers["content-type"] == "application/pdf"
        assert pdf_res.content.startswith(b"%PDF-")


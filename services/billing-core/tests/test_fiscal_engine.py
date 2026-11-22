"""Unit tests for the agricultural fiscal engine, Spanish NIF/CIF validator, and sequencer."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.database import Base
from src.services.fiscal_engine import calculate_reagp_invoice, validate_spanish_id
from src.services.sequence_service import get_next_invoice_number


# ---------------------------------------------------------------------------
# Test 1: Spanish NIF/CIF/NIE Validation
# ---------------------------------------------------------------------------
class TestSpanishIDValidation:
    def test_valid_dni(self):
        # 12345678Z is a classic valid DNI test
        assert validate_spanish_id("12345678Z") is True

    def test_invalid_dni(self):
        # Wrong check letter
        assert validate_spanish_id("12345678A") is False
        assert validate_spanish_id("1234") is False
        assert validate_spanish_id("") is False

    def test_valid_nie(self):
        # X1234567L is valid NIE
        assert validate_spanish_id("X1234567L") is True

    def test_valid_cif_cooperatives_and_corporations(self):
        # F23112233: Cooperative from Hito 1 examples
        assert validate_spanish_id("F23112233") is True
        # A41558899: S.A. from Hito 1 examples
        assert validate_spanish_id("A41558899") is True
        # B23987451: S.L. from Hito 1 examples
        assert validate_spanish_id("B23987451") is True

    def test_invalid_cif(self):
        assert validate_spanish_id("F23112239") is False
        assert validate_spanish_id("Z99999999") is False


# ---------------------------------------------------------------------------
# Test 2: REAGP Agricultural Fiscal Calculations
# ---------------------------------------------------------------------------
class TestREAGPFiscalEngine:
    def test_us03_olive_oil_harvest_invoice_calculation(self):
        """Validates US-03: 10,000 kg at 1.00 €/kg under REAGP (+12% compensation, -2% IRPF).

        Base: 10,000.00 €
        Compensación REAGP (+12%): 1,200.00 €
        Retención IRPF (-2%): 200.00 €
        Total a percibir: 11,000.00 €
        """
        items = [{"description": "Aceituna Picual (kg)", "quantity": 10000.0, "unit_price": 1.00}]

        result = calculate_reagp_invoice(
            items=items,
            tax_regime="REAGP",
            compensation_pct=12.0,
            withholding_pct=2.0,
        )

        assert result["taxable_base"] == 10000.00
        assert result["compensation_pct"] == 12.0
        assert result["compensation_amount"] == 1200.00
        assert result["withholding_pct"] == 2.0
        assert result["withholding_amount"] == 200.00
        assert result["total_invoice"] == 11000.00

    def test_hito1_multi_item_invoice_calculation(self):
        """Validates Hito 1 multi-item scenario:

        - 12,500 kg @ 0.88 € = 11,000.00 €
        - 1 transporte @ 150.00 € = 150.00 €
        Base = 11,150.00 €
        Compensación REAGP (12%) = 1,338.00 €
        Retención IRPF (2%) = 223.00 €
        Total = 12,265.00 €
        """
        items = [
            {"description": "Aceituna Picual Campaña 2026/2027 (kg)", "quantity": 12500.0, "unit_price": 0.88},
            {"description": "Porte y transporte a almazara", "quantity": 1.0, "unit_price": 150.00},
        ]

        result = calculate_reagp_invoice(
            items=items,
            tax_regime="REAGP",
            compensation_pct=12.0,
            withholding_pct=2.0,
        )

        assert result["taxable_base"] == 11150.00
        assert result["compensation_amount"] == 1338.00
        assert result["withholding_amount"] == 223.00
        assert result["total_invoice"] == 12265.00

    def test_livestock_reagp_compensation(self):
        """Livestock regime REAGP applies 10.5% flat compensation."""
        items = [{"description": "Ganado ovino (cabezas)", "quantity": 50.0, "unit_price": 80.00}]
        # Base: 4,000.00 €
        # Compensación 10.5%: 420.00 €
        # Retención 2%: 80.00 €
        # Total: 4,340.00 €
        result = calculate_reagp_invoice(
            items=items,
            tax_regime="REAGP",
            compensation_pct=10.5,
            withholding_pct=2.0,
        )

        assert result["taxable_base"] == 4000.00
        assert result["compensation_amount"] == 420.00
        assert result["withholding_amount"] == 80.00
        assert result["total_invoice"] == 4340.00


# ---------------------------------------------------------------------------
# Test 3: Concurrency and Strict Sequence Generator
# ---------------------------------------------------------------------------
class TestSequenceGenerator:
    def test_atomic_sequence_consecutive_generation(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        session_factory = sessionmaker(bind=engine)
        db = session_factory()

        seq1 = get_next_invoice_number(db, 2026)
        db.commit()
        seq2 = get_next_invoice_number(db, 2026)
        db.commit()
        seq3 = get_next_invoice_number(db, 2026)
        db.commit()

        assert seq1 == "AGR-2026-001"
        assert seq2 == "AGR-2026-002"
        assert seq3 == "AGR-2026-003"
        db.close()

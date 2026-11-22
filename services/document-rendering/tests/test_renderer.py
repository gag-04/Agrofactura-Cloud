"""Unit tests for HTML template compilation and binary PDF rendering engine."""

from src.engine.renderer import compile_html, render_pdf


def test_html_template_compilation():
    context = {
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
    }

    html = compile_html("invoice_template.html", context)
    assert "AGR-2026-001" in html
    assert "Explotaciones Agrícolas San Isidro" in html
    assert "Almazara Cooperativa Ntra. Sra. de la Oliva" in html
    assert "11150.00 €" in html
    assert "12265.00 €" in html
    assert "REAGP" in html


def test_pdf_binary_rendering():
    html_content = """
    <html>
        <body>
            <h1>Factura de Prueba</h1>
            <p>Contenido oficial para comprobación de PDF binario.</p>
        </body>
    </html>
    """
    pdf_bytes, elapsed_ms = render_pdf(html_content)

    assert isinstance(pdf_bytes, bytes)
    # Check standard PDF magic header
    assert pdf_bytes.startswith(b"%PDF-")
    assert len(pdf_bytes) > 500
    assert elapsed_ms >= 0

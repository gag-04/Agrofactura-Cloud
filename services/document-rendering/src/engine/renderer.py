"""Jinja2 compilation and PDF rendering engine."""

import io
import os
import time
from typing import Any, Dict, Tuple

from jinja2 import Environment, FileSystemLoader, select_autoescape
from xhtml2pdf import pisa

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")
env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html", "xml"]),
)


def compile_html(template_name: str, context: Dict[str, Any]) -> str:
    """Compiles a Jinja2 HTML template with invoice payload context."""
    template = env.get_template(template_name)
    return template.render(**context)


def render_pdf(html_content: str) -> Tuple[bytes, int]:
    """Compiles HTML into a high-fidelity binary PDF buffer.

    Returns:
        Tuple of (pdf_bytes, elapsed_time_ms)
    """
    start_time = time.perf_counter()
    pdf_buffer = io.BytesIO()

    pisa_status = pisa.CreatePDF(
        src=html_content,
        dest=pdf_buffer,
        encoding="utf-8",
    )

    elapsed_ms = int((time.perf_counter() - start_time) * 1000)

    if pisa_status.err:
        raise RuntimeError(f"Error rendering PDF document: {pisa_status.err}")

    return pdf_buffer.getvalue(), elapsed_ms

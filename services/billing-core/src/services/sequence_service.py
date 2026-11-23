"""Atomic sequence generator for strict correlative invoicing."""

from sqlalchemy.orm import Session

from src.models.db_models import InvoiceSequence


def get_next_invoice_number(db: Session, year: int) -> str:
    """Atomically allocates the next consecutive invoice number for a fiscal year.

    Ensures compliance with Royal Decree 1619/2012, Ley 11/2021 (Antifraude),
    and VeriFactu regulations:
    - Guaranteed sequential numbering (e.g. AGR-2026-001, AGR-2026-002).
    - Prevents chronological gaps and duplicate sequences under concurrent transactions.
    """
    seq_entry = (
        db.query(InvoiceSequence)
        .filter(InvoiceSequence.year == year)
        .with_for_update()
        .first()
    )

    if not seq_entry:
        seq_entry = InvoiceSequence(year=year, last_sequence=1)
        db.add(seq_entry)
        db.flush()
        next_seq = 1
    else:
        seq_entry.last_sequence += 1
        db.flush()
        next_seq = seq_entry.last_sequence

    return f"AGR-{year}-{next_seq:03d}"

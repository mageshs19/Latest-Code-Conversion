# LOCATION: converter/generators/db2_infrastructure/spec_builder/spec_fixed_format.py
# ACTION: CREATE NEW FILE
"""Extracts the body of one fixed-format source record.

CORRECTION - the geometry was inlined twice and wrong at the edge.

    body = raw[7:] if len(raw) > 7 else raw
    if len(body) > 65:
        body = body[:65]

appeared in _materialised_records() and again in the LRF scanner. On a
record SHORTER than eight characters the `else raw` branch returned the
LEFT SEQUENCE NUMBER as if it were COBOL, so a stray numeric line could
match a statement pattern. One implementation, derived from the column
boundaries.
"""

from __future__ import annotations

from rules.cursor_spec import BODY_END_INDEX, BODY_START_INDEX


def body_of(record: str) -> str:
    """Columns 8-72 of a fixed-format record, stripped.

    A record shorter than the body window yields "" rather than its own
    sequence area.
    """
    text = str(record or "").rstrip("\r\n")
    if len(text) <= BODY_START_INDEX:
        return ""
    return text[BODY_START_INDEX:BODY_END_INDEX].strip()


def bodies_of(cobol_text: str) -> list[str]:
    """Every record of a program reduced to its body, order preserved.

    Blank bodies are KEPT so an index into this list still addresses the
    same physical record - the LRF scanner reads the NEXT line.
    """
    return [body_of(line) for line in str(cobol_text or "").split("\n")]


__all__ = ["body_of", "bodies_of"]
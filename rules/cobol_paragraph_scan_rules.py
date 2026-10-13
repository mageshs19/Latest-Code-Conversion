# LOCATION: rules/cobol_paragraph_scan_rules.py
# ACTION: CREATE NEW FILE

"""Constants for resolving the paragraph a statement sits inside.

WHY AN EXCLUSION SET IS REQUIRED
    patterns/cobol_cleanup_patterns.PARAGRAPH_HEADER_PATTERN is

        ^(?P<name>[A-Z0-9][A-Z0-9-]*)\\.$

    which is correct for its original consumer but does not know a
    paragraph header from a one-word sentence. Scanning BACKWARDS from a
    statement, the first line it matches is almost always the END-EXEC.
    or CONTINUE. immediately above - not the paragraph header. Reporting
    END-EXEC as the enclosing paragraph would then feed "END-EXEC" into
    SQL-LOCATION.

    Widening the regex was rejected: it has an existing consumer in
    composers/cleanup/paragraph_terminator_cleanup.py and changing a
    shared pattern to suit a second caller is how the SQL-LOCATION
    defect started.

BLAST RADIUS
    PARAGRAPH_SCAN_LIMIT caps the backward walk. A statement further
    than this from any header means the structure is not what we think
    it is, and refusing is better than attributing it to whatever turns
    up next.
"""

from __future__ import annotations

# One-word COBOL sentences that are NOT paragraph headers.
NON_PARAGRAPH_SENTENCE_WORDS = frozenset(
    {
        "CONTINUE",
        "END-EVALUATE",
        "END-EXEC",
        "END-IF",
        "END-PERFORM",
        "END-READ",
        "END-SEARCH",
        "END-STRING",
        "EXIT",
        "GOBACK",
    }
)

PARAGRAPH_SCAN_LIMIT = 200

__all__ = [
    "NON_PARAGRAPH_SENTENCE_WORDS",
    "PARAGRAPH_SCAN_LIMIT",
]
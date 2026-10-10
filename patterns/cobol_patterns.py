"""
COBOL regex patterns.

This module contains regex patterns only.

No business rules.
No runtime logic.
No hardcoded program names, table names, fields, or cursor names.
"""

from __future__ import annotations

import re


PROGRAM_ID_PATTERN = re.compile(
    r"^\s*(?:\d{6})?\s*PROGRAM-ID\.\s+"
    r"(?P<program>[A-Z0-9-]+)\.",
    flags=re.IGNORECASE | re.MULTILINE,
)

DIVISION_PATTERN = re.compile(
    r"^(IDENTIFICATION|ENVIRONMENT|DATA|PROCEDURE)\s+DIVISION\b.*\.?$",
    flags=re.IGNORECASE,
)

PARAGRAPH_PATTERN = re.compile(
    r"^[A-Z0-9][A-Z0-9-]*\.?$",
    flags=re.IGNORECASE,
)

PROCEDURE_DIVISION_PATTERN = re.compile(
    r"^\s*PROCEDURE\s+DIVISION\b",
    flags=re.IGNORECASE,
)

STOP_RUN_PATTERN = re.compile(
    r"^STOP\s+RUN\s*\.?$",
    flags=re.IGNORECASE,
)

GOBACK_PATTERN = re.compile(
    r"^GOBACK\s*\.?$",
    flags=re.IGNORECASE,
)

from __future__ import annotations

import re

PROCEDURE_DIVISION_PATTERN = re.compile(
    r"^PROCEDURE\s+DIVISION\b",
    flags=re.IGNORECASE,
)

DIVISION_PATTERN = re.compile(
    r"^[A-Z][A-Z0-9-]*\s+DIVISION\b",
    flags=re.IGNORECASE,
)

SECTION_HEADER_PATTERN = re.compile(
    r"^(?P<name>[A-Z0-9][A-Z0-9-]*)\s+SECTION\s*\.$",
    flags=re.IGNORECASE,
)

PARAGRAPH_HEADER_PATTERN = re.compile(
    r"^(?P<name>[A-Z0-9][A-Z0-9-]*)\s*\.$",
    flags=re.IGNORECASE,
)

INITIALIZE_PATTERN = re.compile(
    r"^INITIALIZE\s+(?P<group>[A-Z0-9][A-Z0-9-]*)\s*\.?$",
    flags=re.IGNORECASE,
)

DCLGEN_INCLUDE_PATTERN = re.compile(
    r"(?:EXEC\s+SQL\s+INCLUDE|\bCOPY)\s+(?P<group>DCL\w+)\b",
    flags=re.IGNORECASE,
)

DCLGEN_REFERENCE_PATTERN = re.compile(
    r"(?::|\bOF\s+)(?P<group>DCL\w+)\b",
    flags=re.IGNORECASE,
)

HOST_GROUP_PATTERN = re.compile(
    r":\s*(?P<group>DCL[A-Z0-9-]+)\s*\.",
    flags=re.IGNORECASE,
)

PERFORM_OPEN_CURSOR_PATTERN = re.compile(
    r"^PERFORM\s+(?P<number>\d{3,6})-OPEN-(?P<cursor>[A-Z0-9][A-Z0-9-]*)"
    r"\s*\.?$",
    flags=re.IGNORECASE,
)

FETCH_PARAGRAPH_HEADER_PATTERN = re.compile(
    r"^(?P<number>\d{3,6})-FETCH-(?P<cursor>[A-Z0-9][A-Z0-9-]*)\s*\.$",
    flags=re.IGNORECASE,
)

CURSOR_PARAGRAPH_HEADER_PATTERN = re.compile(
    r"^(?P<number>\d{3,6})-(?P<operation>OPEN|FETCH|CLOSE)-"
    r"(?P<cursor>[A-Z0-9][A-Z0-9-]*)\s*\.$",
    flags=re.IGNORECASE,
)

PERFORM_PARAGRAPH_PATTERN = re.compile(
    r"^PERFORM\s+(?P<paragraph>[A-Z0-9][A-Z0-9-]*)\s*\.?$",
    flags=re.IGNORECASE,
)

LITERAL_PROGRAM_MOVE_PATTERN = re.compile(
    r"^MOVE\s+'[^']+'\s+TO\s+PROGRAM-NAME\s*\.?$",
    flags=re.IGNORECASE,
)
COBOL_HOST_GROUP_PATTERN = re.compile(
    r"\b(?:OF|IN)\s+(?P<group>DCL[A-Z0-9-]+)\b",
    flags=re.IGNORECASE,
)

__all__ = [
    "PROCEDURE_DIVISION_PATTERN",
    "DIVISION_PATTERN",
    "SECTION_HEADER_PATTERN",
    "PARAGRAPH_HEADER_PATTERN",
    "INITIALIZE_PATTERN",
    "DCLGEN_INCLUDE_PATTERN",
    "DCLGEN_REFERENCE_PATTERN",
    "HOST_GROUP_PATTERN",
    "PERFORM_OPEN_CURSOR_PATTERN",
    "FETCH_PARAGRAPH_HEADER_PATTERN",
    "CURSOR_PARAGRAPH_HEADER_PATTERN",
    "PERFORM_PARAGRAPH_PATTERN",
    "LITERAL_PROGRAM_MOVE_PATTERN",
    "COBOL_HOST_GROUP_PATTERN"
]
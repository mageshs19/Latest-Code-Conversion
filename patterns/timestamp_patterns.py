from __future__ import annotations

import re

PROCEDURE_DIVISION_PATTERN = re.compile(
    r"^PROCEDURE\s+DIVISION\b",
    flags=re.IGNORECASE,
)

WORKING_STORAGE_PATTERN = re.compile(
    r"^WORKING-STORAGE\s+SECTION\s*\.",
    flags=re.IGNORECASE,
)

LINKAGE_SECTION_PATTERN = re.compile(
    r"^LINKAGE\s+SECTION\s*\.",
    flags=re.IGNORECASE,
)

END_PROGRAM_PATTERN = re.compile(
    r"^END\s+PROGRAM\b",
    flags=re.IGNORECASE,
)

STOP_RUN_PATTERN = re.compile(
    r"^STOP\s+RUN\s*\.?$",
    flags=re.IGNORECASE,
)

EXEC_SQL_PATTERN = re.compile(
    r"^EXEC\s+SQL\b",
    flags=re.IGNORECASE,
)

END_EXEC_PATTERN = re.compile(
    r"^END-EXEC\s*\.?$",
    flags=re.IGNORECASE,
)

DB2_WRITE_OPERATION_PATTERN = re.compile(
    r"^(INSERT|UPDATE|DELETE)\b",
    flags=re.IGNORECASE,
)

COBOL_WRITE_OPERATION_PATTERN = re.compile(
    r"^(STORE|MODIFY|ERASE)\b",
    flags=re.IGNORECASE,
)

LEVEL_ENTRY_PATTERN = re.compile(
    r"^(?P<level>\d{2})\s+(?P<name>[A-Z0-9][A-Z0-9-]*)\b",
    flags=re.IGNORECASE,
)

STANDALONE_LEVEL_PATTERN = re.compile(
    r"^(?P<level>77|01)\s+(?P<name>[A-Z0-9][A-Z0-9-]*)\b",
    flags=re.IGNORECASE,
)


def declaration_pattern(field: str) -> re.Pattern:
    return re.compile(
        rf"^(?P<level>\d{{2}})\s+{re.escape(str(field))}\b",
        flags=re.IGNORECASE,
    )


def paragraph_header_pattern(name: str) -> re.Pattern:
    return re.compile(
        rf"^{re.escape(str(name))}\s*\.$",
        flags=re.IGNORECASE,
    )


def perform_pattern(name: str) -> re.Pattern:
    return re.compile(
        rf"^PERFORM\s+{re.escape(str(name))}\b",
        flags=re.IGNORECASE,
    )

def literal_move_pattern(field: str) -> re.Pattern:
    return re.compile(
        rf"^MOVE\s+'[^']*'\s+TO\s+{re.escape(str(field))}\s*\.?$",
        flags=re.IGNORECASE,
    )


def constant_move_pattern(constant: str, field: str) -> re.Pattern:
    return re.compile(
        rf"^MOVE\s+{re.escape(str(constant))}\s+TO\s+"
        rf"{re.escape(str(field))}\s*\.?$",
        flags=re.IGNORECASE,
    )

__all__ = [
    "COBOL_WRITE_OPERATION_PATTERN",
    "DB2_WRITE_OPERATION_PATTERN",
    "END_EXEC_PATTERN",
    "END_PROGRAM_PATTERN",
    "EXEC_SQL_PATTERN",
    "LEVEL_ENTRY_PATTERN",
    "LINKAGE_SECTION_PATTERN",
    "PROCEDURE_DIVISION_PATTERN",
    "STANDALONE_LEVEL_PATTERN",
    "STOP_RUN_PATTERN",
    "WORKING_STORAGE_PATTERN",
    "declaration_pattern",
    "paragraph_header_pattern",
    "perform_pattern",
    "literal_move_pattern",
    "constant_move_pattern",
]
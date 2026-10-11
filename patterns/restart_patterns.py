# LOCATION: patterns/restart_patterns.py
# ACTION: REPLACE HEADER BLOCK
r"""Restart / checkpoint regex patterns.

This module contains regex patterns only.

No business rules, no layout constants, no service logic, and no
hardcoded program, paragraph, record, table, DCLGEN, cursor or host
variable names.

All patterns are matched against an already-stripped LOGICAL line:
sequence area (1-6), indicator (7) and identification area (73-80)
removed, trimmed, uppercased.

CORRECTION 1 - a parenthesis was written as an anchor

LEVEL_77_WITH_VALUE_PATTERN read

    PIC\s+X$(?P<size>\d+)$

where the dollar sign is an END-OF-STRING ANCHOR, not a literal
parenthesis. The expression could never match any input, so the legacy
abend-marker detector silently found nothing on every program. This is
the same defect the review engine recorded against CHK-04, where the
equivalent picture test made its criterion skip with "not declared"
forever. A regex that cannot match is worse than a missing one: it
reports success.

Every literal parenthesis in this module is now escaped properly, and
this docstring is raw so the examples above do not themselves become
invalid escape sequences.

CORRECTION 2 - the payload length was a constant, not a measurement

The checkpoint payload length used to be declared in rules/ as a fixed
number. It is actually the sum of the PICTURE sizes of the two
restart-record subfields, which differ per program. PICTURE_SIZE_PATTERN
exists so the resolver measures the program instead of assuming it.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------
# Structural anchors
# ---------------------------------------------------------------------

PARAGRAPH_HEADER_PATTERN = re.compile(
    r"^(?P<name>[A-Z0-9][A-Z0-9-]*)\.$",
    flags=re.IGNORECASE,
)

# The numeric prefix of a generated paragraph name: 700-SELECT-X -> 700.
PARAGRAPH_NUMBER_PATTERN = re.compile(
    r"^(?P<number>\d+)-",
)

PROCEDURE_DIVISION_PATTERN = re.compile(
    r"^PROCEDURE\s+DIVISION\b",
    flags=re.IGNORECASE,
)

WORKING_STORAGE_PATTERN = re.compile(
    r"^WORKING-STORAGE\s+SECTION\s*\.?$",
    flags=re.IGNORECASE,
)

FILE_SECTION_PATTERN = re.compile(
    r"^FILE\s+SECTION\s*\.?$",
    flags=re.IGNORECASE,
)

LINKAGE_SECTION_PATTERN = re.compile(
    r"^LINKAGE\s+SECTION\s*\.?$",
    flags=re.IGNORECASE,
)

# ---------------------------------------------------------------------
# Mainline landmarks
# ---------------------------------------------------------------------

OPEN_INPUT_PATTERN = re.compile(
    r"^OPEN\s+INPUT\s+(?P<file>[A-Z0-9][A-Z0-9-]*)\s*\.?$",
    flags=re.IGNORECASE,
)

CLOSE_FILE_PATTERN = re.compile(
    r"^CLOSE\s+(?P<file>[A-Z0-9][A-Z0-9-]*)\s*\.?$",
    flags=re.IGNORECASE,
)

STOP_RUN_PATTERN = re.compile(
    r"^STOP\s+RUN\s*\.?$",
    flags=re.IGNORECASE,
)

# Both driving-loop idioms the converter supports:
#     PERFORM <para> UNTIL <condition>
#     PERFORM <para> THRU <para>-EXIT UNTIL <condition>
PERFORM_UNTIL_PATTERN = re.compile(
    r"^PERFORM\s+(?P<paragraph>[A-Z0-9][A-Z0-9-]*)"
    r"(?:\s+THRU\s+[A-Z0-9][A-Z0-9-]*)?"
    r"\s+UNTIL\s+(?P<condition>.+?)\s*\.?$",
    flags=re.IGNORECASE,
)

PERFORM_SIMPLE_PATTERN = re.compile(
    r"^PERFORM\s+(?P<paragraph>[A-Z0-9][A-Z0-9-]*)\s*\.?$",
    flags=re.IGNORECASE,
)

# ---------------------------------------------------------------------
# Name discovery in the DATA DIVISION
# ---------------------------------------------------------------------

LEVEL_88_PATTERN = re.compile(
    r"^88\s+(?P<name>[A-Z0-9][A-Z0-9-]*)\s+VALUE\s+"
    r"['\"](?P<value>[^'\"]*)['\"]\s*\.?$",
    flags=re.IGNORECASE,
)

ELEMENTARY_ITEM_PATTERN = re.compile(
    r"^(?P<level>\d{2})\s+(?P<name>[A-Z0-9][A-Z0-9-]*)\s+"
    r"PIC\s+(?P<picture>[A-Z0-9()SV.,+-]+)",
    flags=re.IGNORECASE,
)

# Size declared by a PICTURE clause: PIC 9(15), PIC X(1200), PIC 9(7).
# The repetition factor is what matters; usage (COMP-3) is ignored.
PICTURE_SIZE_PATTERN = re.compile(
    r"^PIC(?:TURE)?\s+(?:IS\s+)?[9XASVZ][(](?P<size>\d+)[)]",
    flags=re.IGNORECASE,
)

FD_PATTERN = re.compile(
    r"^FD\s+(?P<file>[A-Z0-9][A-Z0-9-]*)\b",
    flags=re.IGNORECASE,
)

READ_INTO_PATTERN = re.compile(
    r"^READ\s+(?P<file>[A-Z0-9][A-Z0-9-]*)\s+INTO\s+"
    r"(?P<record>[A-Z0-9][A-Z0-9-]*)\b",
    flags=re.IGNORECASE,
)

# Both the one-line and the split fixed-format shapes:
#     EXEC SQL INCLUDE <member> END-EXEC.
#     INCLUDE <member>
SQL_INCLUDE_PATTERN = re.compile(
    r"^(?:EXEC\s+SQL\s+)?INCLUDE\s+(?P<name>[A-Z0-9][A-Z0-9_-]*)"
    r"(?:\s+END-EXEC)?\s*\.?$",
    flags=re.IGNORECASE,
)
# A 77-level header whose VALUE wrapped onto the following line.
LEVEL_77_HEADER_PATTERN = re.compile(
    r"^77\s+(?P<name>[A-Z0-9][A-Z0-9-]*)\s+PIC\s+[9X][(](?P<size>\d+)[)]"
    r"\s*\.?$",
    flags=re.IGNORECASE,
)

# The continuation line carrying that VALUE.
VALUE_LINE_PATTERN = re.compile(
    r"^VALUE\s+['\"](?P<value>[^'\"]*)['\"]\s*\.?$",
    flags=re.IGNORECASE,
)

# ---------------------------------------------------------------------
# Legacy restart residue
# ---------------------------------------------------------------------
# Matched by SHAPE, never by a site-specific field name. A legacy abend
# marker is a 77-level PIC X(nn) whose VALUE carries the marker prefix;
# the prefix itself lives in rules/, not here.

LEVEL_77_WITH_VALUE_PATTERN = re.compile(
    r"^77\s+(?P<name>[A-Z0-9][A-Z0-9-]*)\s+PIC\s+[9X][(](?P<size>\d+)[)]\s+"
    r"VALUE\s+(?:['\"](?P<value>[^'\"]*)['\"]|(?P<numeric>[-+0-9]+))"
    r"\s*\.?$",
    flags=re.IGNORECASE,
)

INLINE_COMMIT_PATTERN = re.compile(
    r"^EXEC\s+SQL\s*$|^COMMIT\s*$|^END-EXEC\s*\.?$",
    flags=re.IGNORECASE,
)

ORPHAN_SCOPE_TERMINATOR_PATTERN = re.compile(
    r"^END-(?P<verb>IF|EVALUATE|PERFORM|READ|STRING)\s*[.]?\s*$",
    flags=re.IGNORECASE,
)

DOUBLE_PERIOD_PATTERN = re.compile(r"\.\s*\.\s*$")

# A sequence number that leaked into the body:
#     EXEC SQL INCLUDE DZ01RSTV END-EXEC.008300
TRAILING_SEQUENCE_LEAK_PATTERN = re.compile(
    r"(?P<body>\S)\s*(?P<leak>\d{6,8})\s*$",
)

__all__ = [
    "CLOSE_FILE_PATTERN",
    "DOUBLE_PERIOD_PATTERN",
    "ELEMENTARY_ITEM_PATTERN",
    "FD_PATTERN",
    "FILE_SECTION_PATTERN",
    "INLINE_COMMIT_PATTERN",
    "LEVEL_77_HEADER_PATTERN",
    "LEVEL_77_WITH_VALUE_PATTERN",
    "LEVEL_88_PATTERN",
    "LINKAGE_SECTION_PATTERN",
    "OPEN_INPUT_PATTERN",
    "ORPHAN_SCOPE_TERMINATOR_PATTERN",
    "PARAGRAPH_HEADER_PATTERN",
    "PARAGRAPH_NUMBER_PATTERN",
    "PERFORM_SIMPLE_PATTERN",
    "PERFORM_UNTIL_PATTERN",
    "PICTURE_SIZE_PATTERN",
    "PROCEDURE_DIVISION_PATTERN",
    "READ_INTO_PATTERN",
    "SQL_INCLUDE_PATTERN",
    "STOP_RUN_PATTERN",
    "TRAILING_SEQUENCE_LEAK_PATTERN",
    "VALUE_LINE_PATTERN",
    "WORKING_STORAGE_PATTERN",
]
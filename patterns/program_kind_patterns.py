# LOCATION: patterns/program_kind_patterns.py
# ACTION: CREATE NEW FILE

"""Regex for program-kind detection. PATTERNS ONLY.

No conversion logic, no business rules, no names.

WHY THE OLD DETECTOR MISSED EVERYTHING
--------------------------------------
The shape in use elsewhere is::

    r"^\\s*(?:\\d{6}\\s+)?(STORE|MODIFY|ERASE)\\b"

``(?:\\d{6}\\s+)?`` demands WHITESPACE after the six-digit sequence area.
Column 7 is the INDICATOR area and legitimately holds '*', '/', '-' or
'D'. On any line whose indicator is not blank - every comment, every
page eject, every debug line, and every line a previous pass commented
out - the sequence number was never consumed and the verb never matched.

These patterns take a LOGICAL BODY: columns 8-72, already stripped of
both sequence areas and of the indicator, upper-cased and
whitespace-collapsed. No pattern here carries a sequence prefix.
"""

from __future__ import annotations

import re

# An IDMS write verb opening a statement.
IDMS_WRITE_VERB_PATTERN = re.compile(
    r"^(?P<verb>STORE|MODIFY|ERASE)\s+(?P<target>[A-Z0-9][A-Z0-9-]*)",
    flags=re.IGNORECASE,
)

# The Logical Record Facility form of the same verbs:
#     MODIFY <logical-record> WHERE <keyword>.
IDMS_WRITE_LRF_PATTERN = re.compile(
    r"^(?P<verb>STORE|MODIFY|ERASE)\s+(?P<target>[A-Z0-9][A-Z0-9-]*)"
    r"\s+WHERE\s+(?P<keyword>[A-Z0-9][A-Z0-9-]*)",
    flags=re.IGNORECASE,
)

# Embedded SQL that writes. A program may already be partly converted.
SQL_WRITE_VERB_PATTERN = re.compile(
    r"^(?:EXEC\s+SQL\s+)?(?P<verb>INSERT|UPDATE|DELETE)\b",
    flags=re.IGNORECASE,
)

# A conversion marker left by an earlier pass is EVIDENCE that a write
# verb existed, even though the verb itself has been commented away.
CONVERTED_WRITE_MARKER_PATTERN = re.compile(
    r"^\*\s*DB2:\s*Converted\s+(?P<verb>STORE|MODIFY|ERASE)\b",
    flags=re.IGNORECASE,
)

KEEP_WRITE_MARKER_PATTERN = re.compile(
    r"^\*\s*DB2-KEEP\b.*\b(?P<verb>STORE|MODIFY|ERASE)\b",
    flags=re.IGNORECASE,
)

__all__ = [
    "IDMS_WRITE_VERB_PATTERN",
    "IDMS_WRITE_LRF_PATTERN",
    "SQL_WRITE_VERB_PATTERN",
    "CONVERTED_WRITE_MARKER_PATTERN",
    "KEEP_WRITE_MARKER_PATTERN",
]
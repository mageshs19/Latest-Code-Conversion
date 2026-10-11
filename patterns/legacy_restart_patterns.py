# LOCATION: patterns/legacy_restart_patterns.py
# ACTION: CREATE NEW FILE

"""Regex for the legacy restart generator.

This module contains PATTERNS ONLY.

No conversion logic, no business rules, no layout constants, and no
program, paragraph, record, table, DCLGEN, cursor or host variable
name. Anything a pattern must match by NAME is supplied as an argument
to a builder below, never baked into a compiled pattern.

WHY THE BUILDERS EXIST
----------------------
A paragraph, a group or an include can only be located by its name, and
that name is resolved at runtime. Compiling a literal would put site
vocabulary in patterns/. Each builder takes the resolved name, escapes
it, and returns a compiled pattern scoped to that one name.

ALL MATCHING IS AGAINST A LOGICAL BODY
--------------------------------------
Callers pass columns 8-72, already stripped of both sequence areas and
of the indicator, upper-cased and whitespace-collapsed. No pattern here
carries an optional ``(?:\\d{6}\\s+)?`` prefix. The previous generator
did, and it still missed every line whose column 7 was not blank -
which is every comment, every page eject and every debug line.
"""

from __future__ import annotations

import re

# =====================================================================
# Division and section anchors
# =====================================================================
IDENTIFICATION_DIVISION_PATTERN = re.compile(
    r"^IDENTIFICATION\s+DIVISION\b", flags=re.IGNORECASE
)
DATA_DIVISION_PATTERN = re.compile(
    r"^DATA\s+DIVISION\b", flags=re.IGNORECASE
)
PROCEDURE_DIVISION_PATTERN = re.compile(
    r"^PROCEDURE\s+DIVISION\b", flags=re.IGNORECASE
)
FILE_SECTION_PATTERN = re.compile(
    r"^FILE\s+SECTION\b", flags=re.IGNORECASE
)
WORKING_STORAGE_PATTERN = re.compile(
    r"^WORKING-STORAGE\s+SECTION\b", flags=re.IGNORECASE
)
LINKAGE_SECTION_PATTERN = re.compile(
    r"^LINKAGE\s+SECTION\b", flags=re.IGNORECASE
)

# Any line that ENDS the WORKING-STORAGE SECTION.
WORKING_STORAGE_END_PATTERN = re.compile(
    r"^(?:LINKAGE\s+SECTION|PROCEDURE\s+DIVISION|LOCAL-STORAGE\s+SECTION)\b",
    flags=re.IGNORECASE,
)

# =====================================================================
# Program identity
# =====================================================================
PROGRAM_ID_PATTERN = re.compile(
    r"^PROGRAM-ID\s*\.\s*(?P<name>[A-Z0-9][A-Z0-9-]*)",
    flags=re.IGNORECASE,
)

# =====================================================================
# Data description
# =====================================================================
LEVEL_01_PATTERN = re.compile(r"^01\s+\S", flags=re.IGNORECASE)
LEVEL_77_PATTERN = re.compile(r"^77\s+\S", flags=re.IGNORECASE)

ANY_LEVEL_PATTERN = re.compile(
    r"^(?P<level>0?[1-9]|[1-4][0-9]|6[0-9]|7[0-7]|88)\s+"
    r"(?P<name>[A-Z0-9][A-Z0-9-]*)",
    flags=re.IGNORECASE,
)

# 88 <name> VALUE 'Y'. - a candidate end-of-file condition.
LEVEL_88_TRUE_PATTERN = re.compile(
    r"^88\s+(?P<name>[A-Z0-9][A-Z0-9-]*)\s+VALUE\s+'(?P<value>[^']*)'",
    flags=re.IGNORECASE,
)

PICTURE_SIZE_PATTERN = re.compile(
    r"PIC(?:TURE)?\s+(?:IS\s+)?(?P<picture>[^.\s]+)",
    flags=re.IGNORECASE,
)

# =====================================================================
# Procedure structure
# =====================================================================
PARAGRAPH_HEADER_PATTERN = re.compile(
    r"^(?P<name>[A-Z0-9][A-Z0-9-]*)\s*\.$", flags=re.IGNORECASE
)

TERMINATION_PATTERN = re.compile(
    r"^(?:STOP\s+RUN|GOBACK|EXIT\s+PROGRAM)\s*\.?$", flags=re.IGNORECASE
)

CLOSE_STATEMENT_PATTERN = re.compile(
    r"^CLOSE\s+(?P<file>[A-Z0-9][A-Z0-9-]*)", flags=re.IGNORECASE
)

OPEN_STATEMENT_PATTERN = re.compile(
    r"^OPEN\s+(?:INPUT|OUTPUT|I-O|EXTEND)\s+(?P<file>[A-Z0-9][A-Z0-9-]*)",
    flags=re.IGNORECASE,
)

PERFORM_PATTERN = re.compile(
    r"^PERFORM\s+(?P<paragraph>[A-Z0-9][A-Z0-9-]*)", flags=re.IGNORECASE
)

PERFORM_UNTIL_PATTERN = re.compile(
    r"^PERFORM\s+(?P<paragraph>[A-Z0-9][A-Z0-9-]*)\s+UNTIL\s+"
    r"(?P<condition>.+)$",
    flags=re.IGNORECASE,
)

EXECUTABLE_START_PATTERN = re.compile(
    r"^(?:PERFORM|MOVE|INITIALIZE|OPEN|CLOSE|READ|WRITE|SET|ADD|"
    r"SUBTRACT|COMPUTE|IF|EVALUATE|CALL|DISPLAY|EXEC)\b",
    flags=re.IGNORECASE,
)

# =====================================================================
# End-of-file detection
# =====================================================================
# AT END MOVE 'Y' TO <switch>
AT_END_MOVE_PATTERN = re.compile(
    r"\bAT\s+END\b.*?\bTO\s+(?P<switch>[A-Z0-9][A-Z0-9-]*)",
    flags=re.IGNORECASE,
)

# AT END SET <condition> TO TRUE
AT_END_SET_PATTERN = re.compile(
    r"\bAT\s+END\b\s*SET\s+(?P<condition>[A-Z0-9][A-Z0-9-]*)\s+TO\s+TRUE",
    flags=re.IGNORECASE,
)

# =====================================================================
# Embedded SQL
# =====================================================================
EXEC_SQL_OPEN_PATTERN = re.compile(
    r"^EXEC\s+SQL\b", flags=re.IGNORECASE
)
EXEC_SQL_CLOSE_PATTERN = re.compile(
    r"^END-EXEC\s*\.?$", flags=re.IGNORECASE
)
SQL_INCLUDE_PATTERN = re.compile(
    r"^EXEC\s+SQL\s+INCLUDE\s+(?P<name>[A-Z0-9#@$-]+)\s+END-EXEC",
    flags=re.IGNORECASE,
)
SQL_VERB_PATTERN = re.compile(
    r"^(?P<verb>SELECT|INSERT|UPDATE|DELETE|OPEN|FETCH|CLOSE|COMMIT|"
    r"ROLLBACK|DECLARE|INCLUDE)\b",
    flags=re.IGNORECASE,
)

# =====================================================================
# Conversion markers left by earlier passes
# =====================================================================
CONVERTED_UPDATE_MARKER_PATTERN = re.compile(
    r"^\*\s*DB2:\s*Converted\s+(?P<verb>STORE|MODIFY|ERASE)\s+for\s+"
    r"(?P<record>[A-Z0-9][A-Z0-9-]*)",
    flags=re.IGNORECASE,
)

KEEP_MARKER_PATTERN = re.compile(
    r"^\*\s*DB2-KEEP\b", flags=re.IGNORECASE
)

# =====================================================================
# Hygiene checks on GENERATED output
# =====================================================================
# A six-to-eight digit run glued to the end of a statement. This is the
# signature of a block spliced onto the front of the next physical line,
# carrying that line's sequence number into the body.
SEQUENCE_BLEED_PATTERN = re.compile(r"[A-Z0-9)\.]\d{6,8}\s*$")

# A null sentence: a period alone on a line.
LONE_PERIOD_PATTERN = re.compile(r"^\.\s*$")

# =====================================================================
# Name-scoped pattern builders
# =====================================================================
def paragraph_pattern(name: str) -> re.Pattern[str]:
    """Match exactly the paragraph header ``<name>.``"""
    return re.compile(
        rf"^{re.escape(str(name or '').strip())}\s*\.$",
        flags=re.IGNORECASE,
    )


def perform_pattern(name: str) -> re.Pattern[str]:
    """Match a PERFORM of exactly this paragraph."""
    return re.compile(
        rf"\bPERFORM\s+{re.escape(str(name or '').strip())}\b",
        flags=re.IGNORECASE,
    )


def group_header_pattern(name: str) -> re.Pattern[str]:
    """Match ``01 <name>`` at any 01-level spelling."""
    return re.compile(
        rf"^01\s+{re.escape(str(name or '').strip())}\b",
        flags=re.IGNORECASE,
    )


def data_name_pattern(name: str) -> re.Pattern[str]:
    """Match a whole-word reference to one data name."""
    return re.compile(
        rf"(?<![A-Z0-9-]){re.escape(str(name or '').strip())}"
        rf"(?![A-Z0-9-])",
        flags=re.IGNORECASE,
    )


def include_pattern(name: str) -> re.Pattern[str]:
    """Match an EXEC SQL INCLUDE of exactly this member."""
    return re.compile(
        rf"^EXEC\s+SQL\s+INCLUDE\s+"
        rf"{re.escape(str(name or '').strip())}\s+END-EXEC",
        flags=re.IGNORECASE,
    )


__all__ = [
    "IDENTIFICATION_DIVISION_PATTERN",
    "DATA_DIVISION_PATTERN",
    "PROCEDURE_DIVISION_PATTERN",
    "FILE_SECTION_PATTERN",
    "WORKING_STORAGE_PATTERN",
    "LINKAGE_SECTION_PATTERN",
    "WORKING_STORAGE_END_PATTERN",
    "PROGRAM_ID_PATTERN",
    "LEVEL_01_PATTERN",
    "LEVEL_77_PATTERN",
    "ANY_LEVEL_PATTERN",
    "LEVEL_88_TRUE_PATTERN",
    "PICTURE_SIZE_PATTERN",
    "PARAGRAPH_HEADER_PATTERN",
    "TERMINATION_PATTERN",
    "CLOSE_STATEMENT_PATTERN",
    "OPEN_STATEMENT_PATTERN",
    "PERFORM_PATTERN",
    "PERFORM_UNTIL_PATTERN",
    "EXECUTABLE_START_PATTERN",
    "AT_END_MOVE_PATTERN",
    "AT_END_SET_PATTERN",
    "EXEC_SQL_OPEN_PATTERN",
    "EXEC_SQL_CLOSE_PATTERN",
    "SQL_INCLUDE_PATTERN",
    "SQL_VERB_PATTERN",
    "CONVERTED_UPDATE_MARKER_PATTERN",
    "KEEP_MARKER_PATTERN",
    "SEQUENCE_BLEED_PATTERN",
    "LONE_PERIOD_PATTERN",
    "paragraph_pattern",
    "perform_pattern",
    "group_header_pattern",
    "data_name_pattern",
    "include_pattern",
]
# LOCATION: patterns/idms_patterns.py
# ACTION: REPLACE ENTIRE FILE
"""IDMS regex patterns.

COBOL parsers and IDMS transformers import these patterns instead of
defining IDMS operation regex inside parser or transformer classes.

Regex only. The one name list this module consumes -
REMOVED_COPYBOOK_FIELDS - is imported from rules/, so the vocabulary has
a single owner and the pattern cannot fall behind it.

CORRECTION 1 - a module-level list was mutated at import time
-------------------------------------------------------------
IDMS_DECLARATIVE_OR_CONTROL_PATTERNS was declared as a six-entry list and
then grown by a trailing

    IDMS_DECLARATIVE_OR_CONTROL_PATTERNS.extend([...])

appended under its own "ACTION: APPEND" header. Two consequences:

  - the real contents of the constant could not be read from its own
    declaration, only by scanning the whole file, and
  - a second APPEND block - or a module reload - grows the list again.

This is the defect tests/test_standards_no_duplicate_constants.py found
in cobol_cleanup_patterns.py, where seventeen patterns were declared
twice. The list is now ONE literal.

CORRECTION 2 - the write-verb pattern matched prose
----------------------------------------------------
IDMS_WRITE_VERB_PATTERN was

    \\b(?:STORE|MODIFY|ERASE)\\s+[A-Z][A-Z0-9-]*

unanchored, so the verb matched anywhere on a line. The pattern is read
by ConversionComponentFactory._program_is_update to classify the PROGRAM
KIND from the SOURCE text - comments included. A remark or a DISPLAY
literal containing the word MODIFY classified a read-only program as an
update program, and the COMMIT it does not need was kept.

review/ui/review_panel.py already classifies correctly:

    ^\\s*(?:\\d{6}\\s+)?(STORE|MODIFY|ERASE)\\b

anchored at the start of a logical line, with the fixed-format sequence
area allowed for. Two owners of one question, one of them right. This
module now matches the review engine's form, so the converter and the
reviewer cannot disagree about what an update program is.

CORRECTION 3 - nothing could find a reference to a deleted declaration
-----------------------------------------------------------------------
COPY_IDMS_PATTERN removes every COPY IDMS member, including the two that
DECLARE LR-STATUS, ERROR-STATUS and DML-SEQUENCE. No pattern existed to
find the references those deletions orphan, so

    DISPLAY '##&&LR-STATUS    : ', LR-STATUS.

survived into generated output as an undefined data name.
REMOVED_COPYBOOK_FIELD_PATTERN is that detector. It is built FROM
rules.REMOVED_COPYBOOK_FIELDS, so adding a field there cannot leave the
regex behind.
"""

from __future__ import annotations

import re

from rules.idms_transformer_rules import REMOVED_COPYBOOK_FIELDS

# ---------------------------------------------------------------- retrieval
OBTAIN_CALC_PATTERN = re.compile(
    r"\bOBTAIN\s+(?:KEEP\s+)?(?P<record>[A-Z0-9-]+)\s+CALC\b",
    flags=re.IGNORECASE,
)

OBTAIN_CALC_REVERSED_PATTERN = re.compile(
    r"\bOBTAIN\s+(?:KEEP\s+)?CALC\s+(?P<record>[A-Z0-9-]+)\b",
    flags=re.IGNORECASE,
)

OBTAIN_FIRST_NEXT_PATTERN = re.compile(
    r"\bOBTAIN\s+(?:KEEP\s+)?(?P<mode>FIRST|NEXT)\s+"
    r"(?P<record>[A-Z0-9-]+)\s+WITHIN\s+(?P<set>[A-Z0-9-]+)\b",
    flags=re.IGNORECASE,
)

OBTAIN_OWNER_PATTERN = re.compile(
    r"\bOBTAIN\s+OWNER\s+WITHIN\s+(?P<set>[A-Z0-9-]+)\b",
    flags=re.IGNORECASE,
)

# The record name is optional: FIND FIRST WITHIN <set> is legal IDMS.
# \s* rather than \s+ so the omitted-record form still matches.
FIND_FIRST_PATTERN = re.compile(
    r"\bFIND\s+FIRST\s+(?P<record>[A-Z0-9-]+)?\s*WITHIN\s+"
    r"(?P<set>[A-Z0-9-]+)\b",
    flags=re.IGNORECASE,
)

FIND_CURRENT_PATTERN = re.compile(
    r"^\s*FIND\s+CURRENT\b",
    flags=re.IGNORECASE,
)

# ------------------------------------------------------------------- update
STORE_PATTERN = re.compile(
    r"\bSTORE\s+(?P<record>[A-Z0-9-]+)\b",
    flags=re.IGNORECASE,
)

MODIFY_PATTERN = re.compile(
    r"\bMODIFY\s+(?P<record>[A-Z0-9-]+)\b",
    flags=re.IGNORECASE,
)

ERASE_PATTERN = re.compile(
    r"\bERASE\s+(?P<record>[A-Z0-9-]+)\b",
    flags=re.IGNORECASE,
)

CONNECT_STATEMENT_PATTERN = re.compile(
    r"^\s*CONNECT\b",
    flags=re.IGNORECASE,
)

DISCONNECT_STATEMENT_PATTERN = re.compile(
    r"^\s*DISCONNECT\b",
    flags=re.IGNORECASE,
)

# Program-kind classification. ANCHORED - see CORRECTION 2.
#
# The optional \d{6} is the fixed-format sequence area: this pattern is
# matched against RAW source lines, not stripped logical bodies.
IDMS_WRITE_VERB_PATTERN = re.compile(
    r"^\s*(?:\d{6}\s+)?(?P<verb>STORE|MODIFY|ERASE)\s+"
    r"(?P<record>[A-Z][A-Z0-9-]*)",
    flags=re.IGNORECASE | re.MULTILINE,
)

# ------------------------------------------------------------------ control
READY_PATTERN = re.compile(
    r"^\s*READY\b",
    flags=re.IGNORECASE,
)

READY_UPDATE_PATTERN = re.compile(
    r"\bREADY\s+AREA\s+(?P<record>[A-Z0-9-]+).*UPDATE\b",
    flags=re.IGNORECASE,
)

FINISH_PATTERN = re.compile(
    r"^\s*FINISH\b",
    flags=re.IGNORECASE,
)

COMMIT_PATTERN = re.compile(
    r"^\s*COMMIT\b",
    flags=re.IGNORECASE,
)

BIND_STATEMENT_PATTERN = re.compile(
    r"^\s*BIND\b",
    flags=re.IGNORECASE,
)

USAGE_MODE_PATTERN = re.compile(
    r"\bUSAGE-MODE\s+IS\s+(UPDATE|RETRIEVAL)\b",
    flags=re.IGNORECASE,
)

IDMS_STATUS_PERFORM_PATTERN = re.compile(
    r"\bPERFORM\b.*\bIDMS-STATUS\b",
    flags=re.IGNORECASE,
)

IDMS_ABORT_PERFORM_PATTERN = re.compile(
    r"\bPERFORM\b.*\bIDMS-ABORT\b",
    flags=re.IGNORECASE,
)

# ----------------------------------------------------------- status tokens
DB_REC_NOT_FOUND_TOKEN_PATTERN = re.compile(
    r"\bDB-REC-NOT-FOUND\b",
    flags=re.IGNORECASE,
)

DB_END_OF_SET_TOKEN_PATTERN = re.compile(
    r"\bDB-END-OF-SET\b",
    flags=re.IGNORECASE,
)

ON_DB_REC_NOT_FOUND_PATTERN = re.compile(
    r"^\s*ON\s+DB-REC-NOT-FOUND\b\s*(?P<statement>.+?)?\.?\s*$",
    flags=re.IGNORECASE,
)

# ------------------------------------------- declaratives and control lines
# Named individually so a reader can see WHICH member removes WHAT, and
# so the COPY IDMS entry - the one that orphans field references - is
# addressable on its own.

IDMS_CONTROL_SECTION_PATTERN = re.compile(
    r"^\s*IDMS-CONTROL\s+SECTION\b",
    flags=re.IGNORECASE,
)

PROTOCOL_PATTERN = re.compile(
    r"^\s*PROTOCOL\b",
    flags=re.IGNORECASE,
)

IDMS_RECORDS_WITHIN_PATTERN = re.compile(
    r"^\s*IDMS-RECORDS\s+WITHIN\b",
    flags=re.IGNORECASE,
)

SCHEMA_SECTION_PATTERN = re.compile(
    r"^\s*SCHEMA\s+SECTION\b",
    flags=re.IGNORECASE,
)

DB_RECORD_WITHIN_PATTERN = re.compile(
    r"^\s*DB\s+[A-Z0-9-]+\s+WITHIN\s+[A-Z0-9-]+\b",
    flags=re.IGNORECASE,
)

# Removes EVERY COPY IDMS member, including the two that DECLARE the
# fields in REMOVED_COPYBOOK_FIELDS. Whoever applies this pattern owns
# the surviving references - see REMOVED_COPYBOOK_FIELD_PATTERN below.
COPY_IDMS_PATTERN = re.compile(
    r"^\s*COPY\s+IDMS\b",
    flags=re.IGNORECASE,
)

# PROTOCOL continuation. The statement is
#
#     PROTOCOL. MODE IS BATCH-AUTOSTATUS DEBUG
#               IDMS-RECORDS MANUAL.
#
# Removing only the PROTOCOL line leaves "IDMS-RECORDS MANUAL." behind as
# residual IDMS, which CHK-03 reports and the compiler rejects.
IDMS_RECORDS_CLAUSE_PATTERN = re.compile(
    r"^\s*IDMS-RECORDS\s+(?:MANUAL|AUTOMATIC|WITHIN\b.*)\s*\.?\s*$",
    flags=re.IGNORECASE,
)

MODE_IS_CLAUSE_PATTERN = re.compile(
    r"^\s*MODE\s+IS\s+[A-Z0-9-]+",
    flags=re.IGNORECASE,
)

# ONE literal. Never extended at import time - see CORRECTION 1.
IDMS_DECLARATIVE_OR_CONTROL_PATTERNS = [
    IDMS_CONTROL_SECTION_PATTERN,
    PROTOCOL_PATTERN,
    IDMS_RECORDS_WITHIN_PATTERN,
    SCHEMA_SECTION_PATTERN,
    DB_RECORD_WITHIN_PATTERN,
    COPY_IDMS_PATTERN,
    IDMS_RECORDS_CLAUSE_PATTERN,
    MODE_IS_CLAUSE_PATTERN,
]

# ------------------------------------------- orphaned copybook references
# A whole-word reference to a field whose declaring copybook COPY_IDMS_
# PATTERN removed. Built from the rules tuple so the two cannot drift.
#
# Hyphen is a non-word character, so \b anchors correctly at both ends of
# LR-STATUS. Longest-first so a future field that is a prefix of another
# cannot shadow it.
REMOVED_COPYBOOK_FIELD_PATTERN = re.compile(
    r"\b(?P<field>"
    + "|".join(
        re.escape(name)
        for name in sorted(REMOVED_COPYBOOK_FIELDS, key=len, reverse=True)
    )
    + r")\b",
    flags=re.IGNORECASE,
)

# The two statement forms those references actually take in practice.
# A cleanup pass needs the form to decide between rewriting and
# commenting; the bare pattern above cannot tell them apart.
DISPLAY_STATEMENT_PATTERN = re.compile(
    r"^\s*DISPLAY\b",
    flags=re.IGNORECASE,
)

MOVE_TO_STATEMENT_PATTERN = re.compile(
    r"^\s*MOVE\b.*\bTO\b",
    flags=re.IGNORECASE,
)

IDMS_STOP_PERFORM_PATTERN = re.compile(
    r"\bPERFORM\b.*\bIDMS-STOP\b",
    flags=re.IGNORECASE,
)

__all__ = [
    "IDMS_STOP_PERFORM_PATTERN",
    "BIND_STATEMENT_PATTERN",
    "COMMIT_PATTERN",
    "CONNECT_STATEMENT_PATTERN",
    "COPY_IDMS_PATTERN",
    "DB_END_OF_SET_TOKEN_PATTERN",
    "DB_RECORD_WITHIN_PATTERN",
    "DB_REC_NOT_FOUND_TOKEN_PATTERN",
    "DISCONNECT_STATEMENT_PATTERN",
    "DISPLAY_STATEMENT_PATTERN",
    "ERASE_PATTERN",
    "FIND_CURRENT_PATTERN",
    "FIND_FIRST_PATTERN",
    "FINISH_PATTERN",
    "IDMS_ABORT_PERFORM_PATTERN",
    "IDMS_CONTROL_SECTION_PATTERN",
    "IDMS_DECLARATIVE_OR_CONTROL_PATTERNS",
    "IDMS_RECORDS_CLAUSE_PATTERN",
    "IDMS_RECORDS_WITHIN_PATTERN",
    "IDMS_STATUS_PERFORM_PATTERN",
    "IDMS_WRITE_VERB_PATTERN",
    "MODE_IS_CLAUSE_PATTERN",
    "MODIFY_PATTERN",
    "MOVE_TO_STATEMENT_PATTERN",
    "OBTAIN_CALC_PATTERN",
    "OBTAIN_CALC_REVERSED_PATTERN",
    "OBTAIN_FIRST_NEXT_PATTERN",
    "OBTAIN_OWNER_PATTERN",
    "ON_DB_REC_NOT_FOUND_PATTERN",
    "PROTOCOL_PATTERN",
    "READY_PATTERN",
    "READY_UPDATE_PATTERN",
    "REMOVED_COPYBOOK_FIELD_PATTERN",
    "SCHEMA_SECTION_PATTERN",
    "STORE_PATTERN",
    "USAGE_MODE_PATTERN",
]
# LOCATION: patterns/dynamic_metadata_patterns.py
# ACTION: REPLACE ENTIRE FILE
"""Regex for the dynamic update-program metadata resolver.

Regex only. No program, record, copybook, table, DCLGEN or host variable
name is hardcoded, and no filtering LOGIC lives here - a pattern that
needs a decision captures the surrounding text and lets the resolver
decide.

CORRECTION - the legacy EOF switch had to be spelled with 'Y'

EOF_UNTIL_RE, EOF_IF_RE and EOF_MOVE_RE each require a quoted 'Y'
literal. A program declaring the equally legal numeric form resolved
NOTHING:

    05  SW-EOF  VALUE +0  PIC S9  COMP.
        88 EOF  VALUE +1.
    ...
    AT END MOVE +1 TO SW-EOF.
    PERFORM 200-VERWERK-INFIL UNTIL EOF.
    IF EOF

resolve_legacy_eof_switch() returned "" and the run reported "Legacy EOF
switch not resolved", so the restart family built its own switch, the
reader replacement removed the only write to SW-EOF, and the surviving
`IF EOF` - the restart-replay abend check - became permanently false.

This is the same defect CORRECTION C fixed inside
restart_name_resolver: a switch was matched by NAME SHAPE or by a
LITERAL rather than by MEANING. A switch is a switch whatever its
PICTURE.

The three 'Y'-bound patterns are RETAINED for now so the existing import
in converter/postprocess/update_cobol_file_resolver.py keeps resolving.
They are superseded by EOF_CONDITION_REF_RE / EOF_ANY_MOVE_RE and are to
be deleted once the resolver no longer imports them.
"""

from __future__ import annotations

import re


PROGRAM_RE = re.compile(
    r"\bPROGRAM-ID\s*\.\s*([A-Z0-9_-]+)\s*\.",
    flags=re.IGNORECASE | re.DOTALL,
)

SELECT_RE = re.compile(
    r"\bSELECT\s+([A-Z0-9_-]+)\s+ASSIGN\s+TO\s+([A-Z0-9_-]+)\s*\.",
    flags=re.IGNORECASE | re.DOTALL,
)

READ_RE = re.compile(
    r"\bREAD\s+([A-Z0-9_-]+)(?:\s+INTO\s+([A-Z0-9_-]+))?",
    flags=re.IGNORECASE | re.DOTALL,
)

COPY_RE = re.compile(
    r"\bCOPY\s+([A-Z0-9_-]+)\s*\.",
    flags=re.IGNORECASE,
)

FIELD_USE_RE = re.compile(
    r"\b([A-Z][A-Z0-9-]+)\s+(?:OF|IN)\s+([A-Z][A-Z0-9-]+)\b",
    flags=re.IGNORECASE,
)

MOVE_FIELD_RE = re.compile(
    r"\bMOVE\s+([A-Z][A-Z0-9-]+)\b",
    flags=re.IGNORECASE,
)

SELECT_LINE_RE = re.compile(
    r"\bSELECT\s+([A-Z0-9_-]+)\s+ASSIGN\s+TO\s+([A-Z0-9_-]+)\s*\.",
    flags=re.IGNORECASE,
)

FD_LINE_RE = re.compile(
    r"\bFD\s+([A-Z0-9_-]+)\b",
    flags=re.IGNORECASE,
)

RECORD_CONTAINS_RE = re.compile(
    r"\bRECORD\s+CONTAINS\s+(\d+)\s+CHARACTERS\b",
    flags=re.IGNORECASE,
)

FD_RECORD_01_RE = re.compile(
    r"^\s*01\s+([A-Z0-9_-]+)\b",
    flags=re.IGNORECASE,
)

SECTION_END_RE = re.compile(
    r"\b(WORKING-STORAGE|LINKAGE|PROCEDURE)\s+SECTION\b",
    flags=re.IGNORECASE,
)

READ_LINE_RE = re.compile(
    r"\bREAD\s+([A-Z0-9_-]+)(?:\s+INTO\s+([A-Z0-9_-]+))?",
    flags=re.IGNORECASE,
)

#
# Legacy EOF switch - SUPERSEDED, retained only until the resolver drops
# its import. See the module docstring.
#
EOF_UNTIL_RE = re.compile(
    r"\bUNTIL\s+([A-Z][A-Z0-9-]*)\s*=\s*['\"]Y['\"]",
    flags=re.IGNORECASE,
)

EOF_IF_RE = re.compile(
    r"\bIF\s+(?:NOT\s+)?([A-Z][A-Z0-9-]*)\s*=\s*['\"]Y['\"]",
    flags=re.IGNORECASE,
)

EOF_MOVE_RE = re.compile(
    r"\bMOVE\s+['\"]Y['\"]\s+TO\s+([A-Z][A-Z0-9-]*)\b",
    flags=re.IGNORECASE,
)

#
# Legacy EOF switch - recognised by MEANING
#
# A condition-name reference: UNTIL <name> / IF <name>. Whatever follows
# the name is CAPTURED rather than excluded, because deciding whether it
# is a comparison is logic and belongs in the resolver. That separation
# is what lets the resolver keep "IF EOF" while rejecting
# "IF CO-ID-RS IN DCLDZ01RSTV = '1'".
EOF_CONDITION_REF_RE = re.compile(
    r"\b(?:UNTIL|IF)\s+(?:NOT\s+)?(?P<name>[A-Z][A-Z0-9-]*)",
    flags=re.IGNORECASE,
)

# Any MOVE into a name. The legacy write may be numeric - MOVE +1 TO
# SW-EOF - or alphanumeric - MOVE 'Y' TO SW-EOF.
EOF_ANY_MOVE_RE = re.compile(
    r"\bMOVE\s+\S+\s+TO\s+(?P<name>[A-Z][A-Z0-9-]*)\b",
    flags=re.IGNORECASE,
)

# An 88 declaration, with or without a quoted VALUE. Used to EXCLUDE a
# condition the GENERATED program already declares: a name the generator
# created is by definition not legacy.
DECLARED_88_RE = re.compile(
    r"(?m)^\s*88\s+(?P<name>[A-Z][A-Z0-9-]*)",
    flags=re.IGNORECASE,
)

# Heads that make the preceding name the left side of a comparison
# rather than a condition name.
RELATIONAL_HEAD_RE = re.compile(
    r"^\s*(?:=|<|>|NOT\b|IS\b|EQUAL\b|GREATER\b|LESS\b)",
    flags=re.IGNORECASE,
)

# FIELD OF GROUP / FIELD IN GROUP sits between a name and its operator
# and may repeat. Skipping it is what separates a qualified comparison
# from a condition name.
QUALIFIER_RE = re.compile(
    r"^\s*(?:OF|IN)\s+[A-Z][A-Z0-9-]*",
    flags=re.IGNORECASE,
)

PIC_LENGTH_RE = re.compile(
    r"[X9][(](\d+)[)]|[X9]",
    flags=re.IGNORECASE,
)
# The PROCEDURE DIVISION header. The rewrite below is scoped to the
# procedure so a DATA DIVISION declaration can never be renamed into a
# duplicate 88 - which would not compile.
PROCEDURE_DIVISION_RE = re.compile(
    r"^\s*PROCEDURE\s+DIVISION",
    flags=re.IGNORECASE,
)

# The generated reader's end-of-file write. This is how the LIVE EOF
# condition is READ from the program rather than recomposed from the
# record name for a fourth time.
AT_END_SET_TRUE_RE = re.compile(
    r"\bAT\s+END\s+SET\s+(?P<name>[A-Z][A-Z0-9-]*)\s+TO\s+TRUE\b",
    flags=re.IGNORECASE,
)

# A whole-word occurrence of a condition name. The trailing guard
# rejects a hyphen so a bare "EOF" never matches inside "VMDZ205I-EOF".
CONDITION_WORD_TEMPLATE = r"(?<![A-Z0-9-]){name}(?![A-Z0-9-])"

# Any statement that WRITES a switch or condition. A legacy name that is
# still written is live, and must not be rewritten.
WRITE_TO_NAME_TEMPLATE = (
    r"\b(?:MOVE\s+\S+\s+TO\s+{name}|SET\s+{name}\s+TO\s+TRUE)\b"
)

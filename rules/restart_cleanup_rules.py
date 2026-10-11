# LOCATION: rules/restart_cleanup_rules.py
# ACTION: CREATE NEW FILE
"""Constants for removing legacy restart residue.

This module contains constants only.

No regex patterns, parser logic, service logic, or hardcoded program,
paragraph, record, table, DCLGEN, cursor or host variable names belong
here. The legacy data names below are SITE VOCABULARY, not program
names: they are the fixed working-storage items the pre-DB2 restart
mechanism used, and the same four appear in every program that carried
it.

WHY A SEPARATE RULES MODULE

rules/restart_standard_rules.py owns the shape and policy of the restart
family. Cleanup is a different concern with a different failure mode -
deleting too much - so it gets its own constants and its own reviewer.

NO CONSTANT MAY BE ASSIGNED TWICE IN THIS FILE.
"""

from __future__ import annotations

RESTART_CLEANUP_RULES = [
    "Remove a legacy declaration only when nothing references it.",
    "Remove a restart-family paragraph before regenerating it.",
    "Never remove a paragraph the program still performs, unless it is "
    "being regenerated under the same name.",
    "Report every removal; a silent deletion cannot be reviewed.",
    "Leave anything not understood untouched and say so.",
]

# ---------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------
# Presence of ANY of these means the program already carries a restart
# mechanism of some generation. Detection only - never a removal list.

LEGACY_RESTART_DETECTION_TOKENS = (
    "SW-RECAB",
    "CTR-REC",
    "FFRECAB",
    "NS-REC-FF-IN",
    "READ-FLAT-FILE VARYING",
)

# ---------------------------------------------------------------------
# Removable declarations
# ---------------------------------------------------------------------
# Working-storage items the legacy mechanism owned. Each is removed ONLY
# when the PROCEDURE DIVISION does not reference it: a declaration that
# is still read is load-bearing, whatever its origin.

LEGACY_DECLARATION_NAMES = (
    "SW-RECAB",
    "CTR-REC",
    "FFRECAB",
    "NS-REC-FF-IN",
)

# A legacy abend marker is a 77-level whose VALUE carries this prefix.
# Detected by the literal, never by a program-specific field name.
LEGACY_ABEND_MARKER_PREFIX = "##&&"

NON_PARAGRAPH_DOTTED_LINES = (
    "CONTINUE.",
    "EXIT.",
    "GOBACK.",
    "END-IF.",
    "END-EVALUATE.",
    "END-PERFORM.",
    "END-EXEC.",
)
# How far ahead to look for a VALUE that wrapped onto its own line.
VALUE_CONTINUATION_SCAN_LIMIT = 2

# ---------------------------------------------------------------------
# Boundaries
# ---------------------------------------------------------------------
# A paragraph ends at the next paragraph header, the next section or
# division header, or end of source - whichever comes first.

SECTION_SUFFIX = "SECTION."
DIVISION_SUFFIX = "DIVISION."

# A paragraph longer than this means the boundary test has lost sync, so
# the pass stands down rather than deleting an unknown span.
PARAGRAPH_SPAN_LIMIT = 200

# ---------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------

CLEANUP_MESSAGES = {
    "legacy_detected": (
        "Legacy cleanup: found legacy restart token '{token}'."
    ),
    "legacy_absent": (
        "Legacy cleanup: no legacy restart token found."
    ),
    "paragraph_removed": (
        "Legacy cleanup: removed paragraph {paragraph} ({count} line(s)) "
        "so it can be regenerated."
    ),
    "paragraph_absent": (
        "Legacy cleanup: paragraph {paragraph} not present."
    ),
    "paragraph_too_long": (
        "Legacy cleanup: paragraph {paragraph} spans more than "
        "{limit} lines; left unchanged."
    ),
    "declaration_removed": (
        "Legacy cleanup: removed unreferenced legacy declaration {name}."
    ),
    "declaration_referenced": (
        "Legacy cleanup: legacy declaration {name} is still referenced; "
        "left in place."
    ),
    "marker_removed": (
        "Legacy cleanup: removed legacy abend marker {name}."
    ),
    "no_procedure_division": (
        "Legacy cleanup: no PROCEDURE DIVISION; nothing removed."
    ),
}

__all__ = [
    "CLEANUP_MESSAGES",
    "DIVISION_SUFFIX",
    "LEGACY_ABEND_MARKER_PREFIX",
    "LEGACY_DECLARATION_NAMES",
    "LEGACY_RESTART_DETECTION_TOKENS",
    "NON_PARAGRAPH_DOTTED_LINES",
    "PARAGRAPH_SPAN_LIMIT",
    "RESTART_CLEANUP_RULES",
    "SECTION_SUFFIX",
    "VALUE_CONTINUATION_SCAN_LIMIT",
]
# LOCATION: rules/update_audit_repair_rules.py
# ACTION: CREATE NEW FILE
"""Constants for re-asserting the update audit MOVEs after restart injection.

This module contains constants only.

No regex patterns, parser logic, service logic, or hardcoded program,
paragraph, record, table, DCLGEN, cursor or host variable names belong
here. The two SOURCE field names below are site vocabulary already owned
by the timestamp/audit rules module; they are repeated as an explicit
dependency, not authored here.

WHY THIS MODULE EXISTS

The audit MOVEs are inserted into the business paragraph by the update
postprocess. The restart family then rebuilds that paragraph from a
repaired span and the MOVEs are lost with it. The repair pass driven by
these constants runs AFTER the rebuild and puts them back.

NO CONSTANT MAY BE ASSIGNED TWICE IN THIS FILE.
"""

from __future__ import annotations

#
# Master switch
#
ENFORCE_UPDATE_AUDIT_MOVES = True

#
# Which SET columns are audit columns
#
# Column-prefix driven, never a host-variable name. The restart table's
# own UPDATE carries none of these prefixes and is therefore skipped
# without the pass needing to know the restart table name.
#
AUDIT_TIMESTAMP_COLUMN_PREFIXES = ("TS_UPDATE",)
AUDIT_USERID_COLUMN_PREFIXES = (
    "ID_USERID",
    "NR_USERID",
    "ID_USER",
    "NR_USER",
)

#
# Where the value comes from
#
# Both fields are generated into WORKING-STORAGE by the timestamp pass.
# If either is absent the repair REFUSES and says so: a populated audit
# column with an invented source is worse than an empty one.
#
AUDIT_TIMESTAMP_SOURCE_FIELD = "TS-TIMESTAMP"
AUDIT_USERID_SOURCE_FIELD = "CS-PROGRAM"

#
# Generated statement shape
#
MOVE_TEMPLATE = "MOVE {source} TO {host} OF {group}"
CONTINUATION_SPLIT_TOKEN = " OF "

#
# Fixed-format geometry (0-based string indices)
#
# body = line[7:72], i.e. columns 8-72. A statement sits at column 12,
# which is four body spaces. A continuation sits at column 16.
#
SEQUENCE_WIDTH = 6
INDICATOR_INDEX = 6
BODY_START_INDEX = 7
BODY_END_INDEX = 72
LINE_WIDTH = 80
STATEMENT_INDENT = 4
CONTINUATION_INDENT = 8

#
# Block detection
#
EXEC_SQL_TOKEN = "EXEC SQL"
END_EXEC_TOKEN = "END-EXEC"
UPDATE_VERB = "UPDATE"
SET_KEYWORD = "SET"
BLOCK_SCAN_LIMIT = 60
PARAGRAPH_SCAN_LIMIT = 400

#
# Diagnostics. Report every decision, including the ones that do nothing.
#
MESSAGES = {
    "inserted": (
        "Update audit repair: inserted MOVE {source} TO {host} OF {group} "
        "before the UPDATE in {paragraph}."
    ),
    "already_present": (
        "Update audit repair: {host} is already populated in {paragraph}; "
        "nothing inserted."
    ),
    "no_source": (
        "Update audit repair: {field} is not declared in WORKING-STORAGE; "
        "refused to populate {host}."
    ),
    "no_blocks": (
        "Update audit repair: no UPDATE block carrying audit columns was "
        "found; nothing to repair."
    ),
    "disabled": (
        "Update audit repair: pass disabled by ENFORCE_UPDATE_AUDIT_MOVES."
    ),
    "wrapped": (
        "Update audit repair: the MOVE for {host} did not fit columns "
        "8-72 and was continued on a second line."
    ),
    "summary": (
        "Update audit repair: {inserted} statement(s) inserted, "
        "{skipped} already present, {refused} refused."
    ),
}

__all__ = [
    "AUDIT_TIMESTAMP_COLUMN_PREFIXES",
    "AUDIT_TIMESTAMP_SOURCE_FIELD",
    "AUDIT_USERID_COLUMN_PREFIXES",
    "AUDIT_USERID_SOURCE_FIELD",
    "BLOCK_SCAN_LIMIT",
    "BODY_END_INDEX",
    "BODY_START_INDEX",
    "CONTINUATION_INDENT",
    "CONTINUATION_SPLIT_TOKEN",
    "END_EXEC_TOKEN",
    "ENFORCE_UPDATE_AUDIT_MOVES",
    "EXEC_SQL_TOKEN",
    "INDICATOR_INDEX",
    "LINE_WIDTH",
    "MESSAGES",
    "MOVE_TEMPLATE",
    "PARAGRAPH_SCAN_LIMIT",
    "SEQUENCE_WIDTH",
    "SET_KEYWORD",
    "STATEMENT_INDENT",
    "UPDATE_VERB",
]
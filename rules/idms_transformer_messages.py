# LOCATION: rules/idms_transformer_messages.py
# ACTION: REPLACE ENTIRE FILE

from __future__ import annotations

# IDMS statement transformer message/generated-line templates.
# All *DB2: text lives here so wording stays centralized.
# No regex, no logic, no hardcoded program/record/table names.
#
# CORRECTION - TRANSFORMER_MESSAGES was built by post-hoc assignment.
#
#   TRANSFORMER_MESSAGES["program_kind"] = ...
#
# followed the dictionary literal. Subscript assignment is INVISIBLE to
# tests/test_rules_no_duplicate_constants.py, which is how a duplicate
# key hid in the cursor-close-guarantee catalogue, where
# business_paragraph_unverified was assigned twice and the second
# silently won. The catalogue is now ONE dictionary literal: a duplicate
# key inside a literal is reviewable, a duplicate subscript assignment
# is not.
#
# NOTE - this module deliberately declares no __all__. Adding one now
# would change what `from rules.idms_transformer_messages import *`
# resolves to, and any name omitted by accident becomes an ImportError
# in a consumer this change has no business touching. That belongs in
# its own change, with its own measurement.

# ---- Removed control / declarative ----
REMOVED_CONTROL_STATEMENT_TEMPLATE = (
    "*DB2: Removed residual IDMS control statement: {line}"
)
REMOVED_BIND_TEMPLATE = "*DB2: Removed IDMS BIND statement: {line}"
REMOVED_USAGE_READY_TEMPLATE = "*DB2: Removed IDMS usage/READY statement: {line}"
REMOVED_CONNECT_TEMPLATE = "*DB2: Removed IDMS CONNECT statement: {line}"
REMOVED_DISCONNECT_TEMPLATE = "*DB2: Removed IDMS DISCONNECT statement: {line}"
REMOVED_STATUS_ABORT_TEMPLATE = (
    "*DB2: Removed IDMS status/abort paragraph call: {line}"
)
REMOVED_FIND_CURRENT_TEMPLATE = (
    "*DB2: Removed IDMS FIND CURRENT statement: {line}"
)

# ---- FINISH / COMMIT ----
FINISH_OUTSIDE_PROCEDURE_TEMPLATE = (
    "*DB2: FINISH ignored outside PROCEDURE DIVISION: {line}"
)
FINISH_CONVERTED_TO_COMMIT = "*DB2: IDMS FINISH converted to COMMIT."
COMMIT_OUTSIDE_PROCEDURE_TEMPLATE = (
    "*DB2: COMMIT ignored outside PROCEDURE DIVISION: {line}"
)
FINISH_REMOVED_RETRIEVAL = (
    "* DB2: Removed IDMS FINISH; retrieval program is read-only "
    "and needs no COMMIT."
)

# ---- OBTAIN CALC ----
#
# TWO outcomes exist for an OBTAIN CALC, and only one of them was ever
# emitted:
#
#   Removed   -> the UPDATE semantic. A direct
#                UPDATE ... WHERE <composite key> needs no positioning
#                read, so the access is deleted and a CONTINUE left in
#                its place. Correct for an update program.
#
#   Converted -> the RETRIEVAL semantic. The OBTAIN CALC is the only
#                population of the DCLGEN host group, so it becomes a
#                keyed SELECT. Correct for a retrieval program, and
#                never emitted until now.
#
# CONVERTED_OBTAIN_CALC_TEMPLATE is a CONTRACT, not free text. It is
# read by CONVERTED_OBTAIN_CALC_PATTERN in
# converter/composers/update_sql_cleanup/update_sql_cleanup_patterns.py
# and consumed by ObtainCalcRemover, which strips the generated block
# before a direct UPDATE. Emitting exactly this spelling means the
# update side keeps working with no change at all.
#
# MUST stay byte-compatible with:
#   ^\s*\*?\s*DB2:\s*Converted\s+OBTAIN\s+CALC\s+for\s+(?P<record>[A-Z0-9-]+)\.?\s*$
OBTAIN_CALC_OUTSIDE_PROCEDURE_TEMPLATE = (
    "*DB2: OBTAIN CALC ignored outside PROCEDURE DIVISION: {line}"
)
REMOVED_OBTAIN_CALC_SELECT_TEMPLATE = (
    "*DB2: Removed OBTAIN CALC SELECT for {record}."
)
CONVERTED_OBTAIN_CALC_TEMPLATE = "*DB2: Converted OBTAIN CALC for {record}."
DIRECT_UPDATE_COMPOSITE_KEY = (
    "*DB2: Direct UPDATE will use mapped composite key WHERE clause."
)

# ---- LR keyed parent read (diagnostics, not generated COBOL) ----
LRF_CALC_READ_CONVERTED_TEMPLATE = (
    "LRF keyed read: {record} converted to a keyed SELECT; it is the "
    "parent access of an LRF path in a retrieval program and its row "
    "populates the DCLGEN group every later MOVE reads."
)
LRF_CALC_READ_NO_SQL_TEMPLATE = (
    "LRF keyed read: {record} resolved to a table but SqlGenerator "
    "returned no statement; the line was left to the existing "
    "OBTAIN CALC converter."
)

# ---- OBTAIN FIRST / NEXT ----
OBTAIN_OUTSIDE_PROCEDURE_TEMPLATE = (
    "*DB2: OBTAIN ignored outside PROCEDURE DIVISION: {line}"
)
CONVERTED_OBTAIN_FIRST_TEMPLATE = (
    "*DB2: Converted OBTAIN FIRST {record} WITHIN {set_name}."
)
CONVERTED_OBTAIN_NEXT_TEMPLATE = (
    "*DB2: Converted OBTAIN NEXT {record} WITHIN {set_name}."
)

# ---- FIND FIRST ----
FIND_FIRST_OUTSIDE_PROCEDURE_TEMPLATE = (
    "*DB2: FIND FIRST ignored outside PROCEDURE DIVISION: {line}"
)
CONVERTED_FIND_FIRST_TEMPLATE = (
    "*DB2: Converted FIND FIRST {record} WITHIN {set_name}."
)

# ---- STORE / MODIFY / ERASE ----
STORE_MODIFY_ERASE_OUTSIDE_PROCEDURE_TEMPLATE = (
    "*DB2: {operation} ignored outside PROCEDURE DIVISION: {line}"
)

# ---- Generated PERFORM lines for cursor flow ----
PERFORM_OPEN_CURSOR_TEMPLATE = "PERFORM OPEN-{cursor}."
PERFORM_FETCH_CURSOR_TEMPLATE = "PERFORM FETCH-{cursor}."

# ---- Operation names (used in STORE/MODIFY/ERASE messaging) ----
OPERATION_STORE = "STORE"
OPERATION_MODIFY = "MODIFY"
OPERATION_ERASE = "ERASE"

# ---- Residual cleanup ----
REMOVED_REDUNDANT_OBTAIN_NEXT = (
    "*DB2: Removed redundant OBTAIN NEXT after cursor EOC loop."
)
REMOVED_REDUNDANT_SQLCODE_WRAPPER = (
    "*DB2: Removed redundant SQLCODE wrapper after cursor EOC loop."
)
REMOVED_FIELD_LINE_TEMPLATE = (
    "*DB2: Removed {field} operand; its copybook declaration was "
    "deleted by the IDMS conversion. Original: {line}"
)
REMOVED_FIELD_REFUSED_TEMPLATE = (
    "*DB2 WARNING: {field} is undefined after copybook removal but "
    "shares a line with live operands; left for manual review."
)
ERROR_STATUS_MOVE_OWNED_ELSEWHERE = (
    "Residual cleanup: MOVE ... TO ERROR-STATUS left in place; "
    "CobolCleanupComposer converts it into the SW-STATUS-D flag and the "
    "child-fetch early stop."
)

# ---- Diagnostics. ONE dictionary literal. See the CORRECTION above. ----
TRANSFORMER_MESSAGES = {
    "commit_emitted": (
        "Control statement: FINISH converted to COMMIT (update program)."
    ),
    "commit_suppressed": (
        "Control statement: FINISH removed without COMMIT; retrieval "
        "programs are read-only (EMIT_COMMIT_IN_RETRIEVAL = False)."
    ),
    "program_kind": (
        "Program kind: classified as {kind}; COMMIT policy emit_commit={emit}."
    ),
}
# The marker written ABOVE a generated LR keyed read.
#
# Deliberately NOT CONVERTED_OBTAIN_CALC_TEMPLATE. That spelling is
# matched by CONVERTED_OBTAIN_CALC_PATTERN, whose only consumer is
# ObtainCalcRemover - and that pass CONSUMES the SQL block behind the
# marker and replaces it with
#
#     *DB2: Removed OBTAIN CALC SELECT for <record>.
#     *DB2: Direct UPDATE will use mapped composite key WHERE clause.
#     CONTINUE.
#
# which is correct before a direct UPDATE and wrong for a retrieval
# program, where the keyed SELECT is the only population of the DCLGEN
# host group. Reusing the contract looked safe and was not: the only
# consumer of that contract deletes the statement.
#
# MUST NOT match:
#   ^\s*\*?\s*DB2:\s*Converted\s+OBTAIN\s+CALC\s+for\s+(?P<record>[A-Z0-9-]+)\.?\s*$
LRF_CALC_READ_MARKER_TEMPLATE = (
    "*DB2: LRF keyed parent read for {record} -> keyed SELECT."
)

"""
COBOL cleanup rule constants.

This file contains COBOL post-conversion cleanup constant values and message
text only. No regex patterns and no runtime logic belong here.
Rules belong in rules/, patterns in patterns/.
"""

# Generated Working-Storage declaration for the DB2 status flag.
SW_STATUS_D_DECLARATION = (
    "    10  SW-STATUS-D              PIC X    VALUE 'N'."
)

# Generated flag group line used when no WS-STATUS anchor exists.
# NOTE: This literal is emitted into the converted COBOL output, so its value
# is preserved exactly to avoid changing generated program behavior.
WS_DB2_FLAGS_GROUP = " 01  WS-DB2-FEEDBACK-FLAGS."

# Statement starters that stop the backward MOVE-block scan.
STOP_BACKWARD_SCAN_WORDS = (
    "IF ",
    "ELSE",
    "END-IF",
    "PERFORM ",
    "EVALUATE ",
    "WHEN ",
    "WRITE ",
    "EXEC SQL",
    "END-EXEC",
    "OPEN ",
    "CLOSE ",
    "READ ",
    "STOP ",
    "EXIT",
)

# Cursor paragraph number at/above which a fetch is treated as child/nested.
CHILD_FETCH_MINIMUM_NUMBER = 800

# Look-back / look-ahead window sizes.
MOVE_N_LOOKBACK_WINDOW = 3
OUTPUT_MOVE_SCAN_WINDOW = 60
INITIALIZE_LOOKBACK_WINDOW = 3

# LOCATION: rules/cobol_cleanup_rules.py
# ACTION: REPLACE the entire CLEANUP_MESSAGES = { ... } dictionary with this

CLEANUP_MESSAGES = {
    "added_dclgen_include": (
        "Cleanup: added missing DCLGEN include {table}."
    ),
    "replaced_error_status": (
        "Cleanup: replaced ERROR-STATUS move with SW-STATUS-D flag."
    ),
    "declared_sw_status_d_ws": (
        "Cleanup: declared SW-STATUS-D working-storage flag."
    ),
    "declared_sw_status_d_block": (
        "Cleanup: declared SW-STATUS-D in generated flag block."
    ),
    "child_fetch_early_stop": (
        "Cleanup: added SW-STATUS-D early-stop to child fetch loop."
    ),
    "moved_initialize": (
        "Cleanup: moved INITIALIZE before output population for {record}."
    ),
    "converted_db2_date_move": (
        "Cleanup: converted DB2 date move before output write."
    ),
    "removed_residual_idms_comment": (
        "Cleanup: removed residual IDMS conversion comment noise."
    ),
    "removed_orphan_continue": (
        "Cleanup: removed redundant CONTINUE after removed IDMS statement."
    ),
}

# LOCATION: rules/update_sql_cleanup_rules.py
# ACTION: APPEND these constants to the existing file (add at the end)

# --- Category E: manual-standard UPDATE block ---

# QUERYNO value appended to generated SQL statements (manual standard).
# The manual programmer uses the line/paragraph number; we emit a stable
# generated value so DB2 EXPLAIN can identify the statement.
UPDATE_QUERYNO = "442"

# When True, generated UPDATE uses EVALUATE SQLCODE (manual standard) instead
# of the older IF SQLCODE NOT = 0 form.
USE_EVALUATE_SQLCODE = True


# =========================================================================
# APPENDED: constants for the generated-COBOL safety cleanup passes
#
# Consumed by:
#   composers/cleanup/output_write_placement_cleanup.py
#   composers/cleanup/paragraph_terminator_cleanup.py
#
# Constants only. No regex, no runtime logic, no program / record / table /
# cursor / host variable names.
# =========================================================================

# --- Paragraph termination -----------------------------------------------
#
# A paragraph whose last sentence carries no period runs into the next
# paragraph header and the compiler rejects the program. Any pass that
# inserts or lifts a block can leave that state behind.
ENFORCE_PARAGRAPH_TERMINATION = True
PARAGRAPH_TERMINATOR = "."

# Single-word lines that end in a period but are NOT paragraph headers.
# Declared here so the cleanup family has no cross-rules dependency.
NON_PARAGRAPH_SINGLE_WORDS = frozenset({
    "CONTINUE",
    "END-EXEC",
    "END-EVALUATE",
    "END-IF",
    "END-PERFORM",
    "END-READ",
    "END-SEARCH",
    "END-STRING",
    "END-WRITE",
    "EXIT",
    "GOBACK",
    "STOP",
})

# --- Output write placement ----------------------------------------------
#
# Manual reference shape:
#
#     PERFORM <close-child>
#
#     IF NOT SW-STATUS-D = 'Y'
#        IF <status-field> = '<value>'
#           PERFORM <write-paragraph>
#        END-IF
#     END-IF.
#
# A guarded WRITE left inside the per-row paragraph fires once per fetched
# child row instead of once per parent row.
ENFORCE_OUTPUT_WRITE_AFTER_CHILD_LOOP = True

FETCH_PARAGRAPH_CURSOR_SEPARATOR = "-FETCH-"
NESTED_INDENT_STEP = "   "
WHEN_ZERO_PERFORM_SCAN_LIMIT = 5
OUTPUT_WRITE_MOVE_PASS_LIMIT = 8

EARLY_STOP_FLAG = "SW-STATUS-D"
EARLY_STOP_VALUE = "'Y'"
EARLY_STOP_GUARD_OPEN = "IF NOT {flag} = {value}"
EARLY_STOP_GUARD_CLOSE = "END-IF"

# --- Diagnostics ----------------------------------------------------------
CLEANUP_MESSAGES["output_write_moved"] = (
    "Cleanup: moved output write block from {source} to {target} after the "
    "child cursor loop."
)
CLEANUP_MESSAGES["paragraph_terminated"] = (
    "Cleanup: closed unterminated sentence in paragraph {paragraph}."
)

STATEMENT_CONTINUATION_TOKENS = (
    "TO",
    "FROM",
    "INTO",
    "BY",
    "OF",
    "IN",
    "GIVING",
    "AND",
    "OR",
    "NOT",
    "=",
    ",",
)

# LOCATION: rules/cobol_cleanup_rules.py
# ACTION: APPEND to CLEANUP_MESSAGES

CLEANUP_MESSAGES["output_write_no_row_paragraph"] = (
    "Output write placement: child FETCH {fetch} performs no business "
    "paragraph under WHEN ZERO; the write block was left in place."
)
CLEANUP_MESSAGES["output_write_no_close_perform"] = (
    "Output write placement: no PERFORM of the {cursor} CLOSE paragraph "
    "was found outside the generated cursor paragraphs."
)
CLEANUP_MESSAGES["output_write_no_block"] = (
    "Output write placement: {source} has no trailing IF ... WRITE ... "
    "END-IF block to relocate."
)

CLEANUP_MESSAGES["db2_date_no_output_move"] = (
    "DB2 date output: no DB2 DATE host is moved to an output date field "
    "in this program ({count} candidate move(s) examined)."
)
CLEANUP_MESSAGES["db2_date_no_output_move"] = (
    "DB2 date output: no DB2 DATE host is moved to an output date field "
    "({examined} line(s) examined). Nothing to convert."
)
CLEANUP_MESSAGES["db2_date_move_not_eligible"] = (
    "DB2 date output: {count} DB2 DATE move(s) recognised but none "
    "targeted an output date field; left unchanged."
)
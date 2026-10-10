# LOCATION: rules/cobol_cleanup_rules.py
# ACTION: REPLACE ENTIRE FILE

"""COBOL cleanup rule constants.

Constants and message text only. No regex patterns and no runtime logic
belong here. Rules belong in rules/, patterns in patterns/.

ONE DICTIONARY LITERAL
----------------------
CLEANUP_MESSAGES is declared exactly ONCE, as a single literal. Post-hoc
"CLEANUP_MESSAGES[key] = ..." assignments are what let a duplicate block
hide in a sibling module: Python keeps the LAST assignment, so the first
copy becomes dead text that still reads as authoritative.

CORRECTION 1 - a key was assigned twice with different placeholders.

    CLEANUP_MESSAGES["db2_date_no_output_move"]   ... {count} ...
    CLEANUP_MESSAGES["db2_date_no_output_move"]   ... {examined} ...

The caller renders with .format(examined=...), so the FIRST wording was
unreachable and the SECOND was live. One key, one wording, below.

CORRECTION 2 - a non-existent dictionary was assigned.

    COBOL_CLEANUP_MESSAGES["output_blanking_move_suppressed"] = ...

No such name exists in this module; the dictionary is CLEANUP_MESSAGES.
That line raised NameError at import and took the whole conversion
pipeline down with it.

CORRECTION 3 - constants belonging to another module lived here.

UPDATE_QUERYNO and USE_EVALUATE_SQLCODE are owned by
rules/update_sql_rules.py. A second copy here is a second place to edit
and one commit away from the QUERYNO 254-vs-119 divergence. They are
removed. Import them from their owner; never re-declare.
"""

from __future__ import annotations

# =========================================================================
# Generated Working-Storage literals
#
# These are emitted into the converted COBOL, so their values are
# preserved exactly. Changing one changes generated program behaviour.
# =========================================================================

SW_STATUS_D_DECLARATION = (
    "    10  SW-STATUS-D              PIC X    VALUE 'N'."
)

WS_DB2_FLAGS_GROUP = " 01  WS-DB2-FEEDBACK-FLAGS."


# =========================================================================
# Scanning
# =========================================================================

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

# A line ending on one of these cannot end a statement; its operand is on
# the next physical line. Used to assemble LOGICAL statements before any
# pattern is applied.
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

# Cursor paragraph number at/above which a fetch is treated as child.
CHILD_FETCH_MINIMUM_NUMBER = 800

# Look-back / look-ahead window sizes.
MOVE_N_LOOKBACK_WINDOW = 3
OUTPUT_MOVE_SCAN_WINDOW = 60
INITIALIZE_LOOKBACK_WINDOW = 3


# =========================================================================
# Paragraph termination
#
# A paragraph whose last sentence carries no period runs into the next
# paragraph header and the compiler rejects the program. Any pass that
# inserts or lifts a block can leave that state behind.
# =========================================================================

ENFORCE_PARAGRAPH_TERMINATION = True
PARAGRAPH_TERMINATOR = "."

# Single-word lines ending in a period that are NOT paragraph headers.
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


# =========================================================================
# Output write placement
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
# A guarded WRITE left inside the per-row paragraph fires once per
# fetched child row instead of once per parent row.
# =========================================================================

ENFORCE_OUTPUT_WRITE_AFTER_CHILD_LOOP = True

FETCH_PARAGRAPH_CURSOR_SEPARATOR = "-FETCH-"
NESTED_INDENT_STEP = "   "
WHEN_ZERO_PERFORM_SCAN_LIMIT = 5
OUTPUT_WRITE_MOVE_PASS_LIMIT = 8

EARLY_STOP_FLAG = "SW-STATUS-D"
EARLY_STOP_VALUE = "'Y'"
EARLY_STOP_GUARD_OPEN = "IF NOT {flag} = {value}"
EARLY_STOP_GUARD_CLOSE = "END-IF"


# =========================================================================
# Diagnostics - ONE literal, no post-hoc assignment
#
# Every key is consumed by CleanupMessageCollector.add(key, **values).
# A placeholder here must match the kwargs at the call site, or the
# message renders unformatted and the diagnostic is lost.
# =========================================================================

CLEANUP_MESSAGES = {
    # ---- includes and flags
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

    # ---- residual IDMS noise
    "removed_residual_idms_comment": (
        "Cleanup: removed residual IDMS conversion comment noise."
    ),
    "removed_orphan_continue": (
        "Cleanup: removed redundant CONTINUE after removed IDMS "
        "statement."
    ),

    # ---- output record population
    "moved_initialize": (
        "Cleanup: moved INITIALIZE before output population for "
        "{record}."
    ),
    "output_write_moved": (
        "Cleanup: moved output write block from {source} to {target} "
        "after the child cursor loop."
    ),
    "output_write_no_row_paragraph": (
        "Output write placement: child FETCH {fetch} performs no "
        "business paragraph under WHEN ZERO; the write block was left "
        "in place."
    ),
    "output_write_no_close_perform": (
        "Output write placement: no PERFORM of the {cursor} CLOSE "
        "paragraph was found outside the generated cursor paragraphs."
    ),
    "output_write_no_block": (
        "Output write placement: {source} has no trailing IF ... "
        "WRITE ... END-IF block to relocate."
    ),

    # ---- DB2 output dates
    #
    # Three distinct outcomes. One shared message made a successful run
    # read as a failure, because CobolCleanupComposer runs twice per
    # program and the second pass is idempotent.
    "converted_db2_date_move": (
        "Cleanup: converted {count} DB2 date move(s) before the output "
        "write."
    ),
    "db2_date_move_not_eligible": (
        "DB2 date output: {count} DB2 DATE move(s) recognised but none "
        "targeted an output date field; left unchanged."
    ),
    "db2_date_no_output_move": (
        "DB2 date output: no DB2 DATE host is moved to an output date "
        "field ({examined} line(s) examined). Nothing to convert."
    ),
    "output_blanking_move_suppressed": (
        "Cleanup: suppressed {count} MOVE SPACES to an output date "
        "field; the record is already cleared by INITIALIZE and SPACES "
        "is not a legal date value."
    ),

    # ---- structural safety
    "paragraph_terminated": (
        "Cleanup: closed unterminated sentence in paragraph "
        "{paragraph}."
    ),
}


# NO ASSIGNMENT MAY BE ADDED BELOW THIS LINE. An append lands here, and
# an append is exactly what produced the duplicate key and the
# non-existent-dictionary NameError this file just had removed.
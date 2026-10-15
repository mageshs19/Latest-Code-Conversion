# LOCATION: rules/restart_statement_templates.py
# ACTION: REPLACE ENTIRE FILE
"""COBOL statement templates for the restart / checkpoint family.

This module contains constants only.

Every placeholder is filled from RestartConfig at render time. No
program, paragraph, record, table, DCLGEN, cursor or host variable name
is hardcoded here.

COLUMN GEOMETRY - WHAT THIS FILE DOES AND DOES NOT OWN
------------------------------------------------------
A line with NO leading space is a STATEMENT. The shared Area-B indenter
already used by the retrieval path moves it to Area B, so statements
carry no indent here and both program kinds stay byte-identical.

A line WITH leading space is a CONTINUATION. The indenter reports

    Procedure indent: preserved N line(s) carrying their own clause or
    continuation alignment.

and leaves it exactly where this file put it. The leading spaces are
therefore an ABSOLUTE offset from column 8, not a relative hint.

    2 spaces -> column 10 -> AREA A -> the compiler's Area A, and CHK-06
    4 spaces -> column 12 -> Area B (minimum legal)
    6 spaces -> column 14 -> Area B, reading as a continuation

CORRECTION 1 - six continuation lines sat in Area A
----------------------------------------------------
Every "  TO ..." line carried two spaces and rendered at column 10.
CHK-06.06 reported exactly six occurrences on a generated program:

    line 382   TO WS-RESTART-REC.                     <- restart_found
    line 401   TO TE-CH-RS-DATA-LEN OF DCLDZ01RSTV.   <- write_restart
    line 403   TO TE-CH-RS-DATA-TEXT OF DCLDZ01RSTV.  <- write_restart
    line 411   TO KY-RESTART OF WS-RESTART-REC.       <- commit
    line 419   TO TE-CH-RS-DATA-LEN OF DCLDZ01RSTV.   <- commit
    line 421   TO TE-CH-RS-DATA-TEXT OF DCLDZ01RSTV.  <- commit

They are now six spaces. PROCESS_TAIL_TEMPLATE's PERFORM was raised from
three spaces to four for the same reason: it survived only because the
indenter recognises PERFORM as a statement and normalises it. Relying on
that is relying on a classifier, not on the geometry, and it makes the
invariant below unassertable.

CORRECTION 2 - the commit paragraph had no SQLCODE check
---------------------------------------------------------
COMMIT_TEMPLATE ended at "END-EXEC." Every other generated SQL block in
both program kinds evaluates SQLCODE and routes WHEN OTHER to the error
paragraph; this one did not. A failed COMMIT was therefore invisible:
the program carried on, and the checkpoint row it had just written no
longer matched the data it claimed to describe.

rules/update_standard_generator_templates.py carries the same paragraph
as PROCESS_COMMIT_TEMPLATE and DOES evaluate. The two are one template
under two NAMES, which is exactly why the cross-module agreement test
never reported the divergence - that guard is keyed on the name, so two
spellings of one concept are invisible to it.

The branch body matches the manual reference, which displays the input
counter so the operator can see which record the run died on. The
indents - 4 for WHEN, 9 for a branch statement - are the same geometry
rules/restart_sql_templates.py uses for every other SQL paragraph.

INVARIANT, asserted by tests/restart/test_m1_restart_standards.py:
every template line that begins with whitespace carries at least four
leading spaces.

NO CONSTANT MAY BE ASSIGNED TWICE IN THIS FILE.
"""

from __future__ import annotations

# ---------------------------------------------------------------------
# Mainline
# ---------------------------------------------------------------------
# Fixed order. Nothing may be inserted between CLOSE and STOP RUN.

MAIN_FLOW_TEMPLATE = (
    "OPEN INPUT {file_name}.",
    "",
    "PERFORM {control_paragraph}.",
    "",
    "PERFORM {read_paragraph}.",
    "",
    "PERFORM {process_paragraph} UNTIL {eof_condition}.",
    "",
    "PERFORM {commit_paragraph}.",
    "",
    "{totals_block}",
    "CLOSE {file_name}.",
    "STOP RUN.",
)

# ---------------------------------------------------------------------
# control
# ---------------------------------------------------------------------

CONTROL_TEMPLATE = (
    "{control_paragraph}.",
    "MOVE {program_constant} TO {program_id_field} OF {restart_group}.",
    "MOVE {run_date_field}   TO {date_field}       OF {restart_group}.",
    "MOVE {phase_number}     TO {phase_field}      OF {restart_group}.",
    "",
    "PERFORM {select_paragraph}.",
    "",
    "EVALUATE SQLCODE",
    "    WHEN {sqlcode_ok}        PERFORM {restart_found_paragraph}",
    "    WHEN {sqlcode_not_found} PERFORM {write_restart_paragraph}",
    "    WHEN OTHER               PERFORM {error_paragraph}",
    "END-EVALUATE.",
    "",
    "MOVE 0 TO {commit_counter}.",
)
# ---------------------------------------------------------------------
# restart_found
# ---------------------------------------------------------------------
# Two obligations: block a completed run, and reposition a resumed one.

#
# restart_found
#
# Two obligations: block a completed run, and reposition a resumed one.
#
# NESTING IS PART OF THE CONTRACT
#
# The counter MOVE belongs INSIDE the replay loop, before END-PERFORM.
# It was previously emitted after END-PERFORM, which made it a sibling
# of the PERFORM ... TIMES rather than part of its body. The end value of
# {input_counter} is the same either way, so no test caught it and no
# program misbehaved - but the shape no longer matched the manual
# reference the COBOL team reviews against, and a reviewer had to raise
# it by hand on every generated program.
#
# tests/restart/test_m5b_restart_found_nesting.py now asserts the index
# order, so this cannot drift again.
RESTART_FOUND_TEMPLATE = (
    "{restart_found_paragraph}.",
    "MOVE {payload_text_field} OF {restart_group}",
    "      TO {restart_record}.",
    "",
    "IF {status_field} OF {restart_group} = '{status_complete}'",
    "THEN DISPLAY '{complete_message}'",
    "     PERFORM {abend_paragraph}",
    "ELSE PERFORM {read_count_field} OF {restart_record} TIMES",
    "         PERFORM {read_paragraph}",
    "         MOVE {read_count_field} OF {restart_record}",
    "           TO {input_counter}",
    "     END-PERFORM",
    "END-IF.",
)

# ---------------------------------------------------------------------
# write_restart
# ---------------------------------------------------------------------

WRITE_RESTART_TEMPLATE = (
    "{write_restart_paragraph}.",
    "MOVE '{status_incomplete}' TO {status_field}    OF {restart_group}.",
    "MOVE {retention_days}      TO {retention_field} OF {restart_group}.",
    "MOVE 0                     TO {input_counter}.",
    "MOVE {input_counter}       TO {read_count_field} OF {restart_record}.",
    "INITIALIZE {restart_key_field}.",
    "MOVE {payload_length_insert}",
    "      TO {payload_length_field} OF {restart_group}.",
    "MOVE {restart_record}",
    "      TO {payload_text_field}   OF {restart_group}.",
    "",
    "PERFORM {insert_paragraph}.",
)

# ---------------------------------------------------------------------
# commit
# ---------------------------------------------------------------------
# {payload_length_commit} is DELIBERATELY a separate placeholder from
# {payload_length_insert}. The two are not interchangeable: the insert
# writes the measured payload, while the commit value is governed by
# ENFORCE_FULL_PAYLOAD_LENGTH_ON_COMMIT in rules/restart_standard_rules.py.
# This file owns the SHAPE of that distinction and never its VALUE.
#
# The EVALUATE is NOT optional. See CORRECTION 2 in the module docstring:
# a COMMIT whose SQLCODE is never inspected leaves the checkpoint row and
# the data disagreeing, with nothing said.

COMMIT_TEMPLATE = (
    "{commit_paragraph}.",
    "MOVE 0               TO {commit_counter}.",
    "MOVE {input_counter} TO {read_count_field}  OF {restart_record}.",
    "MOVE {input_save_area}",
    "      TO {restart_key_field} OF {restart_record}.",
    "",
    "IF {eof_condition}",
    "THEN MOVE '{status_complete}'   TO {status_field} OF {restart_group}",
    "ELSE MOVE '{status_incomplete}' TO {status_field} OF {restart_group}",
    "END-IF.",
    "",
    "MOVE {payload_length_commit}",
    "      TO {payload_length_field} OF {restart_group}.",
    "MOVE {restart_record}",
    "      TO {payload_text_field}   OF {restart_group}.",
    "",
    "PERFORM {update_paragraph}.",
    "",
    "EXEC SQL",
    "     COMMIT",
    "END-EXEC.",
    "",
    "EVALUATE SQLCODE",
    "    WHEN {sqlcode_ok}",
    "         CONTINUE",
    "    WHEN OTHER",
    "         DISPLAY '{commit_error_message}' {input_counter}",
    "         PERFORM {error_paragraph}",
    "END-EVALUATE.",
)

# ---------------------------------------------------------------------
# abend
# ---------------------------------------------------------------------

ABEND_TEMPLATE = (
    "{abend_paragraph}.",
    "CALL {abend_module}.",
)

# ---------------------------------------------------------------------
# Injected into the business processing paragraph
# ---------------------------------------------------------------------

PROCESS_TAIL_TEMPLATE = (
    "IF {commit_counter} > {commit_threshold}",
    "    PERFORM {commit_paragraph}",
    "END-IF.",
    "",
    "PERFORM {read_paragraph}.",
)

# ---------------------------------------------------------------------
# Reader paragraph
# ---------------------------------------------------------------------

READ_PARAGRAPH_TEMPLATE = (
    "{read_paragraph}.",
    "INITIALIZE {record_name}.",
    "",
    "READ {file_name} INTO {record_name}",
    "     AT END SET {eof_condition} TO TRUE.",
    "",
    "IF {not_eof_condition}",
    "THEN",
    "     ADD +1 TO {commit_counter}",
    "     ADD +1 TO {input_counter}",
    "     MOVE {record_name} TO {input_save_area}",
    "END-IF.",
)

COMPLETE_RUN_MESSAGE = " PREVIOUS RUN COMPLETE "

# Displayed when COMMIT fails. The input counter is appended by the
# template, matching the manual reference: the operator needs the record
# number, not only the fact that something went wrong.
COMMIT_ERROR_MESSAGE = "ERROR REC NUMBER : "

# Minimum leading spaces on a continuation line. Column 8 + 4 = column 12,
# the first column of Area B. Declared so the contract test and this file
# cannot drift apart.
MINIMUM_CONTINUATION_INDENT = 4


__all__ = [
    "ABEND_TEMPLATE",
    "COMMIT_ERROR_MESSAGE",
    "COMMIT_TEMPLATE",
    "COMPLETE_RUN_MESSAGE",
    "CONTROL_TEMPLATE",
    "MAIN_FLOW_TEMPLATE",
    "MINIMUM_CONTINUATION_INDENT",
    "PROCESS_TAIL_TEMPLATE",
    "READ_PARAGRAPH_TEMPLATE",
    "RESTART_FOUND_TEMPLATE",
    "WRITE_RESTART_TEMPLATE",
]
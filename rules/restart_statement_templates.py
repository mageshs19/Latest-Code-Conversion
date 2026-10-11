# LOCATION: rules/restart_statement_templates.py
# ACTION: CREATE NEW FILE
"""COBOL statement templates for the restart / checkpoint family.

This module contains constants only.

Every placeholder is filled from RestartConfig at render time. No
program, paragraph, record, table, DCLGEN, cursor or host variable name
is hardcoded here.

Indentation is NOT applied here. The shared Area-B indenter already used
by the retrieval path owns column geometry, so both program kinds stay
byte-identical in layout.

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

RESTART_FOUND_TEMPLATE = (
    "{restart_found_paragraph}.",
    "MOVE {payload_text_field} OF {restart_group}",
    "  TO {restart_record}.",
    "",
    "IF {status_field} OF {restart_group} = '{status_complete}'",
    "THEN DISPLAY '{complete_message}'",
    "     PERFORM {abend_paragraph}",
    "ELSE PERFORM {read_count_field} OF {restart_record} TIMES",
    "         PERFORM {read_paragraph}",
    "     END-PERFORM",
    "     MOVE {read_count_field} OF {restart_record}",
    "       TO {input_counter}",
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
    "  TO {payload_length_field} OF {restart_group}.",
    "MOVE {restart_record}",
    "  TO {payload_text_field}   OF {restart_group}.",
    "",
    "PERFORM {insert_paragraph}.",
)

# ---------------------------------------------------------------------
# commit
# ---------------------------------------------------------------------

COMMIT_TEMPLATE = (
    "{commit_paragraph}.",
    "MOVE 0               TO {commit_counter}.",
    "MOVE {input_counter} TO {read_count_field}  OF {restart_record}.",
    "MOVE {input_save_area}",
    "  TO {restart_key_field} OF {restart_record}.",
    "",
    "IF {eof_condition}",
    "THEN MOVE '{status_complete}'   TO {status_field} OF {restart_group}",
    "ELSE MOVE '{status_incomplete}' TO {status_field} OF {restart_group}",
    "END-IF.",
    "",
    "MOVE {payload_length_commit}",
    "  TO {payload_length_field} OF {restart_group}.",
    "MOVE {restart_record}",
    "  TO {payload_text_field}   OF {restart_group}.",
    "",
    "PERFORM {update_paragraph}.",
    "",
    "EXEC SQL",
    "     COMMIT",
    "END-EXEC.",
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
    "   PERFORM {commit_paragraph}",
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

__all__ = [
    "ABEND_TEMPLATE",
    "COMMIT_TEMPLATE",
    "COMPLETE_RUN_MESSAGE",
    "CONTROL_TEMPLATE",
    "MAIN_FLOW_TEMPLATE",
    "PROCESS_TAIL_TEMPLATE",
    "READ_PARAGRAPH_TEMPLATE",
    "RESTART_FOUND_TEMPLATE",
    "WRITE_RESTART_TEMPLATE",
]
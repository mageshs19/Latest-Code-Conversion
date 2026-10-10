# LOCATION: rules/counter_rules.py
# ACTION: CREATE NEW FILE
"""Row counter and program-name constant rules.

Closes open decision D-2 (processing counters) in favour of AUTOMATE,
per the COBOL team's manual reference program.

Constants only. No regex, no runtime logic, no program / record / table /
cursor / host variable names.
"""

from __future__ import annotations

# ---------------------------------------------------------------------
# Program-name constant
# ---------------------------------------------------------------------
EMIT_PROGRAM_NAME_CONSTANT = True

PROGRAM_CONSTANT_NAME = "CS-PROGRAM"

# Standard formatting: 28-char field name, PIC X(8), space-aligned VALUE
PROGRAM_CONSTANT_TEMPLATE = (
    "10  {name:<28} PIC X(8)    VALUE '{program_id}'."
)

PROGRAM_NAME_TARGET_FIELD = "PROGRAM-NAME"

# Standard move format: 3 spaces after MOVE, 3 spaces before TO
PROGRAM_NAME_MOVE_TEMPLATE = "MOVE {constant}   TO {target}"

# Style note: formatting ensures alignment with other declarations
PROGRAM_CONSTANT_STYLE_NOTE = (
    "Program constant declaration uses 28-char left-aligned field name, "
    "followed by 'PIC X(8)    VALUE' with proper spacing. This aligns "
    "with standard COBOL formatting across all programs."
)

# ---------------------------------------------------------------------
# Row counters
# ---------------------------------------------------------------------
EMIT_ROW_COUNTERS = True

COUNTER_NAME_TEMPLATE = "WS-NB-{token}-COUNT"
COUNTER_PICTURE = "PIC 9(7)    COMP-3 VALUE ZEROES."
COUNTER_DECLARATION_TEMPLATE = "10  {name:<24} {picture}"

# One counter per cursor (rows fetched) plus one for the output file.
OUTPUT_COUNTER_NAME = "WS-NB-OUTPUT-COUNT"
OUTPUT_COUNTER_TOKEN = "OUTPUT"

COUNTER_ADD_TEMPLATE = "ADD 1 TO {name}"

# ---------------------------------------------------------------------
# End-of-run totals
# ---------------------------------------------------------------------
EMIT_COUNTER_TOTALS = True

COUNTER_DISPLAY_TEMPLATE = "DISPLAY '{label} : ' {name}"
COUNTER_LABEL_WIDTH = 20
COUNTER_LABEL_FETCH_TEMPLATE = "TOTAL {token} RECORDS"
COUNTER_LABEL_OUTPUT = "TOTAL OUTPUT RECORDS"

# Totals are displayed after the output file is closed and before
# STOP RUN, matching the manual reference.
COUNTER_TOTALS_ANCHOR = "CLOSE"

# ---------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------
COUNTER_MESSAGES = {
    "declared_counter": (
        "Counters: declared row counter {name}."
    ),
    "declared_program_constant": (
        "Counters: declared program-name constant {name} = '{program_id}'."
    ),
    "counter_increment_added": (
        "Counters: added increment for {name} in paragraph {paragraph}."
    ),
    "counter_totals_added": (
        "Counters: added {count} end-of-run total display line(s)."
    ),
}
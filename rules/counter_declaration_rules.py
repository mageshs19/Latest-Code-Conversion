# LOCATION: rules/counter_declaration_rules.py
# ACTION: CREATE NEW FILE

"""Row counter declaration rules.

Closes open decision D-2 (processing counters) in favour of AUTOMATE,
per the COBOL team's manual reference program:

    10  WS-NB-BEFF-COUNT         PIC 9(7)    COMP-3 VALUE ZEROES.
    10  WS-NB-OUTPUT-COUNT       PIC 9(7)    COMP-3 VALUE ZEROES.
    ...
    DISPLAY 'TOTAL BEFF RECORDS   : ' WS-NB-BEFF-COUNT
    DISPLAY 'TOTAL OUTPUT RECORDS : ' WS-NB-OUTPUT-COUNT

Declaration is REFERENCE-DRIVEN, not table-driven: the composer declares
exactly the counters the PROCEDURE DIVISION actually increments. It can
therefore never declare an unused field, and never miss one.

Constants only. No regex, no runtime logic, no program / record / table /
cursor / host variable names.
"""

from __future__ import annotations
from rules.counter_rules import COUNTER_TOTALS_ANCHOR

TOTALS_ANCHOR_STATEMENT = COUNTER_TOTALS_ANCHOR
# =====================================================================
# Master switch
# =====================================================================
ENFORCE_COUNTER_DECLARATION = True

# =====================================================================
# Declaration layout
# =====================================================================
# The manual reference declares counters as subordinates of the existing
# 01 work group, at the same level as its other children. The composer
# reads that level from the group rather than assuming one.
COUNTER_DECLARATION_TEMPLATE = "{level}  {name:<24} {picture}"
COUNTER_PICTURE = "PIC 9(7)    COMP-3 VALUE ZEROES."
FALLBACK_CHILD_LEVEL = "10"

# =====================================================================
# End-of-run totals
# =====================================================================
EMIT_COUNTER_TOTALS = True

COUNTER_DISPLAY_TEMPLATE = "DISPLAY '{label} : ' {name}"
COUNTER_LABEL_TEMPLATE = "TOTAL {token} RECORDS"
COUNTER_LABEL_WIDTH = 20


TOTALS_INDENT = "    "

# =====================================================================
# Diagnostics
# =====================================================================
COUNTER_DECLARATION_MESSAGES = {
    "declared": (
        "Counters: declared {name} in {group}."
    ),
    "totals_added": (
        "Counters: added {count} end-of-run total display line(s)."
    ),
    "skipped_no_group": (
        "Counters: no WORKING-STORAGE 01 group found; {count} counter "
        "reference(s) left undeclared."
    ),
    "skipped_no_anchor": (
        "Counters: no {anchor} statement found; end-of-run totals skipped."
    ),
        "no_references": (
        "Counters: no counter increment found in the PROCEDURE "
        "DIVISION ({examined} line(s) examined); nothing declared and "
        "no end-of-run totals emitted."
    ),
}
# LOCATION: rules/counter_declaration_rules.py
# ACTION: APPEND at the end of the file

#
# Counter naming convention
#
# A generated row counter is WS-NB-<token>-COUNT. The token is the
# distinctive middle of the DB2 table name, or OUTPUT for the file
# counter. Kept here so no composer carries a naming literal.
#
COUNTER_NAME_PREFIX = "WS-NB-"
COUNTER_NAME_SUFFIX = "-COUNT"
COUNTER_OUTPUT_TOKEN = "OUTPUT"

# Tokens that identify an existing end-of-run total line.
TOTALS_DISPLAY_VERB = "DISPLAY"
TOTALS_LABEL_TOKEN = "TOTAL"

# LOCATION: rules/counter_declaration_rules.py
# ACTION: APPEND at the end of the file

# ---- Declaration gates -------------------------------------------
# A name rendered with COUNTER_PICTURE must be counter-shaped. Setting
# this False lets any data-name be declared PIC 9(7) COMP-3, which is a
# silent type change on an existing field.
ENFORCE_COUNTER_NAME_SHAPE = True

# A total line is a promise the field is maintained. The totals pass may
# only display names that are actually declared. Setting this False
# restores the defect where WS-NB-EVEF-COUNT was displayed for a table
# this program does not read, showing zero on every run.
ENFORCE_TOTALS_SUBSET_OF_DECLARED = True

COUNTER_DECLARATION_MESSAGES.update({
    "refused_shape": (
        "Counters: {name} is not {prefix}<token>{suffix}; refused "
        "rather than declare it as a packed counter."
    ),
    "refused_duplicate": (
        "Counters: {name} is already declared in the DATA DIVISION; "
        "not declared again."
    ),
    "refused_total": (
        "Counters: {name} is not declared in this program; the "
        "end-of-run total line was not emitted."
    ),
})
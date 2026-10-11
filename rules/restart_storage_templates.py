# LOCATION: rules/restart_storage_templates.py
# ACTION: CREATE NEW FILE
"""Working-storage SHAPES for the restart family.

Constants only. No regex, no logic, no program / paragraph / record /
table / DCLGEN / cursor / host variable names - every name arrives as a
placeholder filled from RestartProgramNames or the storage catalog.

WHAT THIS MODULE DELIBERATELY DOES NOT OWN

    the restart key length    - MEASURED from the source program
    the read count length     - MEASURED from the source program

Both reach the templates as {restart_key_size} and {read_count_size}.
Declaring them here would make the generator the author of a layout it
has no authority over, which is the defect M2 exists to prevent.

NO CONSTANT MAY BE ASSIGNED TWICE IN THIS FILE.
"""

from __future__ import annotations

#
# Master switch
#
ENFORCE_RESTART_STORAGE = True

#
# Values
#
EOF_TRUE_VALUE = "Y"
EOF_FALSE_VALUE = "N"

#
# Elementary item pictures that carry no measurement
#
# The counters are COMP-3 per the manual reference. The two MEASURED
# lengths are not here - see the module docstring.
COMMIT_COUNTER_PICTURE = "PIC 9(9)   COMP-3 VALUE ZERO."
INPUT_COUNTER_PICTURE = "PIC 9(7)   COMP-3 VALUE ZERO."

#
# Group shapes
#
# One blank line separates groups; the Area B pass and the resequencer
# settle the absolute columns afterwards, so the indents below are
# RELATIVE and meaningful only to each other.
#
SWITCH_GROUP_TEMPLATE = (
    "01  {switch_group}.",
    "    02  {eof_switch:<22} PIC X     VALUE '{eof_false}'.",
    "        88  {not_eof_condition:<22} VALUE '{eof_false}'.",
    "        88  {eof_condition:<22} VALUE '{eof_true}'.",
)

HELP_GROUP_TEMPLATE = (
    "01  {help_group}.",
    "    02  {restart_record}.",
    "        03  {read_count_field:<18} PIC 9({read_count_size})"
    "   VALUE ZERO.",
    "        03  {restart_key_field:<18} PIC X({restart_key_size})"
    " VALUE SPACES.",
    "",
    "    02  {input_save_area:<22} PIC X({restart_key_size})"
    " VALUE SPACES.",
    "    02  {commit_counter:<22} " + COMMIT_COUNTER_PICTURE,
    "    02  {input_counter:<22} " + INPUT_COUNTER_PICTURE,
)

#
# The audit MOVEs the business paragraph needs
#
# Emitted only when the business UPDATE sets those columns; the builder
# never guesses that it does.
AUDIT_MOVE_TEMPLATE = (
    "MOVE {timestamp_field} TO {audit_timestamp_column} OF {host_record}.",
    "MOVE {program_constant} TO {audit_user_column} OF {host_record}.",
)

#
# Diagnostics
#
RESTART_STORAGE_MESSAGES = {
    "built": (
        "Restart storage: generated {count} working-storage line(s) for "
        "{groups}."
    ),
    "refused": (
        "Restart storage: {name} unresolved; no working storage emitted."
    ),
    "unmeasured": (
        "Restart storage: {name} was never measured; no working storage "
        "emitted. The checkpoint layout is read from the program, never "
        "assumed."
    ),
    "disabled": (
        "Restart storage: generation is switched off; the program keeps "
        "whatever working storage it already carries."
    ),
}


# NO CONSTANT MAY BE ADDED BELOW THIS LINE.

__all__ = [
    "AUDIT_MOVE_TEMPLATE",
    "COMMIT_COUNTER_PICTURE",
    "ENFORCE_RESTART_STORAGE",
    "EOF_FALSE_VALUE",
    "EOF_TRUE_VALUE",
    "HELP_GROUP_TEMPLATE",
    "INPUT_COUNTER_PICTURE",
    "RESTART_STORAGE_MESSAGES",
    "SWITCH_GROUP_TEMPLATE",
]
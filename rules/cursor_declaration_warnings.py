# LOCATION: rules/cursor_declaration_warnings.py
# ACTION: CREATE NEW FILE
"""DB2 WARNING comment blocks emitted in place of a refused cursor.

EMITTED AS COBOL COMMENT LINES, so each line must fit
WARNING_BODY_WIDTH (65).

cobol_standards.FORBIDDEN_MARKERS contains "DB2 WARNING" deliberately:
a program that still carries one of these must FAIL production
validation rather than ship a cursor that cannot bind.

CORRECTION 7 - the warnings did not fit a COBOL line.

UNRESOLVED_JOIN_KEY_TEMPLATE rendered, with real names, to about 77
characters. The fixed-format composer therefore wrapped or truncated
the one line that explains why the cursor is missing. A diagnostic that
cannot be read is no diagnostic. The *_LINES tuples are sized for the
window.

CORRECTION 20 - WARNING_PREFIX was declared and then re-typed.

The prefix existed as a constant AND as a hardcoded "* DB2 WARNING: "
inside four templates - five copies of one literal, which is
CORRECTION 1's pattern in a file whose whole subject is avoiding it.
Every template is now BUILT from the prefix.

CORRECTION 21 - NO_TABLE_LABEL was missing entirely.

cursor_declare/declare_column_ownership.py imports it. Without it the
module raises ImportError on first import, so the whole declare package
fails to load.
"""

from __future__ import annotations

WARNING_PREFIX = "* DB2 WARNING: "

# Stand-in used in a diagnostic when the spec carries no table at all.
# A label belongs in the catalogue, not in the builder.
NO_TABLE_LABEL = "(none)"

CURSOR_NOT_DECLARED_TEMPLATE = (
    f"{WARNING_PREFIX}Cursor {{cursor}} not declared."
)

UNRESOLVED_JOIN_KEY_LINES = (
    CURSOR_NOT_DECLARED_TEMPLATE,
    f"{WARNING_PREFIX}{{column}} is not a column of {{table}}.",
)

MISSING_COLUMNS_LINES = (
    CURSOR_NOT_DECLARED_TEMPLATE,
    f"{WARNING_PREFIX}No mapped DCLGEN column for {{table}}.",
)

# DEPRECATED single-line forms.
#
# Retained only so an un-migrated caller keeps importing. They OVERFLOW
# the body window with real names and must not be used for new
# emission; use the *_LINES tuples above.
UNRESOLVED_JOIN_KEY_TEMPLATE = (
    f"{WARNING_PREFIX}Unable to declare cursor {{cursor}}; join key "
    "{column} is not a column of {table}."
)
MISSING_COLUMNS_TEMPLATE = (
    f"{WARNING_PREFIX}Unable to declare cursor {{cursor}}; no mapped "
    "DCLGEN column was resolved for {table}."
)

__all__ = [
    "WARNING_PREFIX", "NO_TABLE_LABEL", "CURSOR_NOT_DECLARED_TEMPLATE",
    "UNRESOLVED_JOIN_KEY_LINES", "MISSING_COLUMNS_LINES",
    "UNRESOLVED_JOIN_KEY_TEMPLATE", "MISSING_COLUMNS_TEMPLATE",
]
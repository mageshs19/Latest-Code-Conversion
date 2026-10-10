# LOCATION: rules/cursor_declaration_geometry.py
# ACTION: CREATE NEW FILE
"""Fixed-format geometry for a generated DECLARE CURSOR.

Constants only.

CORRECTION 9 - indents were hand-counted spaces.

Each indent was a space literal with its target column stated only in a
trailing comment, so the comment and the value could disagree and
nothing would notice. Every indent is DERIVED from its column number,
as rules/fixed_format_rules.py derives its widths from the column
boundaries. The rendered strings are byte-identical.

CORRECTION 18 - two indents, one column.

IND_CLAUSE and IND_SELECT_FIRST were computed separately from the SAME
COLUMN_CLAUSE. Identical today, one edit away from disagreeing. The
second is now DERIVED from the first, so the identity is stated rather
than coincidental.

DELIBERATE DUPLICATION - rules/db2_infrastructure_rules.py carries its
own IND_* for the LEGACY CursorDeclarationGenerator, whose output shape
genuinely differs. That file says in terms: do NOT unify them until the
legacy generator is deleted.
"""

from __future__ import annotations

# Columns 1-6 left sequence, column 7 indicator, columns 8-72 body.
BODY_FIRST_COLUMN = 8
BODY_LAST_COLUMN = 72

# A generated comment occupies the indicator column plus the body, so
# its usable width is the body window itself.
WARNING_BODY_WIDTH = BODY_LAST_COLUMN - BODY_FIRST_COLUMN + 1  # 65

# Target column first, indent DERIVED from it.
COLUMN_EXEC = 12         # EXEC SQL, END-EXEC
COLUMN_CLAUSE = 14       # DECLARE, SELECT, FROM, WHERE, ORDER BY
COLUMN_SELECT_NEXT = 19  # leading comma, name aligns under SELECT's
COLUMN_WHERE_NEXT = 16   # AND, under WHERE
COLUMN_QUERYNO = 21      # QUERYNO, indented past FOR READ ONLY

IND_EXEC = " " * (COLUMN_EXEC - BODY_FIRST_COLUMN)
IND_CLAUSE = " " * (COLUMN_CLAUSE - BODY_FIRST_COLUMN)

# SELECT opens a clause, so its first item sits at the clause column.
# DERIVED, not re-computed. See CORRECTION 18.
IND_SELECT_FIRST = IND_CLAUSE

IND_SELECT_NEXT = " " * (COLUMN_SELECT_NEXT - BODY_FIRST_COLUMN)
IND_WHERE_NEXT = " " * (COLUMN_WHERE_NEXT - BODY_FIRST_COLUMN)
IND_QUERYNO = " " * (COLUMN_QUERYNO - BODY_FIRST_COLUMN)

__all__ = [
    "BODY_FIRST_COLUMN", "BODY_LAST_COLUMN", "WARNING_BODY_WIDTH",
    "COLUMN_EXEC", "COLUMN_CLAUSE", "COLUMN_SELECT_NEXT",
    "COLUMN_WHERE_NEXT", "COLUMN_QUERYNO",
    "IND_EXEC", "IND_CLAUSE", "IND_SELECT_FIRST",
    "IND_SELECT_NEXT", "IND_WHERE_NEXT", "IND_QUERYNO",
]
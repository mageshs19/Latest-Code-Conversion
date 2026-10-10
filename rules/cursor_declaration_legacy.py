# LOCATION: rules/cursor_declaration_legacy.py
# ACTION: CREATE NEW FILE
"""Literals belonging ONLY to the legacy CursorDeclarationGenerator.

rules/db2_infrastructure_rules.py says of the duplicated indents:

    "When the legacy generator is deleted, delete its indents with it
     and these become the only copy. Until then, do NOT unify them -
     the output shapes genuinely differ."

This module is the other half of that instruction: the legacy-only
values live HERE, so deleting the legacy generator is one file plus one
import line, not an archaeology exercise.

CORRECTION 1 - three warnings were re-declared inside the generator.

MISSING_CURSOR_NAME, MISSING_TABLE_TEMPLATE and MISSING_COLUMNS_TEMPLATE
were module constants in cursor_declaration_generator.py while
rules/db2_infrastructure_rules.py and rules/cursor_declaration_warnings.py
already owned those names - and the wording had already drifted:

    legacy : "missing DB2 table mapping."
    rules  : "no DB2 table."

Two operators reading two reports of the same refusal saw two
sentences. The generator imports the catalogued text now; nothing is
declared here that another rules module already owns.

CORRECTION 2 - IND_CLAUSE[:-1] stood in for a column.

The WHERE keyword sits one column left of the other clause keywords.
That was expressed by slicing a character off another indent, which
breaks silently the moment COLUMN_CLAUSE moves. It is DERIVED from its
own column number now.
"""

from __future__ import annotations

from rules.cursor_declaration_geometry import BODY_FIRST_COLUMN

# ---------------------------------------------------------------------
# Legacy indents
# ---------------------------------------------------------------------
# WHERE opens one column left of DECLARE / SELECT / FROM in the legacy
# shape. See CORRECTION 2.
COLUMN_WHERE_FIRST = 13

IND_WHERE_FIRST = " " * (COLUMN_WHERE_FIRST - BODY_FIRST_COLUMN)

# ---------------------------------------------------------------------
# Banner short name
# ---------------------------------------------------------------------
# DZBEFFTV -> BEFF. The shop prefixes a DB2 table with two characters
# and suffixes a view with TV / a base table with TB.
TABLE_VIEW_SUFFIXES = ("_TV", "_TB", "TV", "TB")
TABLE_PREFIX_LENGTH = 2
BANNER_NAME_TRIM = "_-"

# ---------------------------------------------------------------------
# QUERYNO
# ---------------------------------------------------------------------
# Cursor order is 1-BASED everywhere else in the project.
# CursorDeclareBuilder renders order 1 as QUERYNO 254; this generator
# enumerated from 0 and rendered 253. Two generators, two numbering
# schemes, one EXPLAIN report. See CORRECTION 3 in the generator.
FIRST_CURSOR_ORDER = 1

__all__ = [
    "COLUMN_WHERE_FIRST", "IND_WHERE_FIRST",
    "TABLE_VIEW_SUFFIXES", "TABLE_PREFIX_LENGTH", "BANNER_NAME_TRIM",
    "FIRST_CURSOR_ORDER",
]
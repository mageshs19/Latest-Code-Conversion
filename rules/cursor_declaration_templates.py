# LOCATION: rules/cursor_declaration_templates.py
# ACTION: CREATE NEW FILE
"""Clause text and QUERYNO for a generated DECLARE CURSOR.

    EXEC SQL DECLARE DZBFASC1 CURSOR WITH HOLD FOR
      SELECT CT_RKTGDSV_479BFAS
           , NR_ID_479BFAS
      FROM DZBFASTV
      ORDER BY NR_ID_479BFAS ASC
      FOR READ ONLY
             QUERYNO 254
    END-EXEC

CORRECTION 2 - QUERYNO did not match the manual reference.

The generated DECLARE carried QUERYNO 119 = 100 + (1 x 19) while manual
reference VMDZ7200 carries 254. DB2 EXPLAIN identifies a statement by
QUERYNO; a number the reference does not use cannot be tied back to the
documented access path.

Cursor order is 1-BASED and the renderer computes

    QUERYNO_BASE + (cursor_order x QUERYNO_STEP)

so QUERYNO_BASE is NOT the first value; it is the value at order 0. It
is DERIVED from the reference value, so changing QUERYNO_FIRST alone
moves every generated number and nothing else is touched.

CORRECTION 3 - the placeholder must stay {number}.

cursor_declare_builder renders with QUERYNO_TEMPLATE.format(number=...)
while rules/db2_infrastructure_rules.py used "{queryno}". Swapping the
two raises KeyError at render time. {number} is the live contract;
db2_infrastructure_rules re-exports from here and assigns nothing.
"""

from __future__ import annotations

# True  -> EXEC SQL DECLARE <cursor> CURSOR WITH HOLD FOR   (manual)
# False -> EXEC SQL / DECLARE <cursor> CURSOR WITH HOLD FOR (two lines)
DECLARE_ON_EXEC_SQL_LINE = True

DECLARE_LINE_TEMPLATE = "EXEC SQL DECLARE {cursor} CURSOR WITH HOLD FOR"
SELECT_FIRST_TEMPLATE = "SELECT {column}"
SELECT_NEXT_TEMPLATE = ", {column}"
FROM_TEMPLATE = "FROM {table}"
WHERE_FIRST_TEMPLATE = "WHERE {condition}"
WHERE_NEXT_TEMPLATE = "AND {condition}"
ORDER_BY_TEMPLATE = "ORDER BY {columns}"
FOR_READ_ONLY = "FOR READ ONLY"
END_EXEC = "END-EXEC"

# Every declaration except the last closes with a bare END-EXEC. The
# last one closes the WORKING-STORAGE sentence with a period, matching
# the manual reference.
LAST_DECLARATION_TERMINATOR = "."

# ---------------------------------------------------------------------
# QUERYNO
# ---------------------------------------------------------------------
# SINGLE SOURCE OF TRUTH. rules/db2_infrastructure_rules.py re-exports
# these names and must never redefine them.
EMIT_QUERYNO = True

QUERYNO_TEMPLATE = "QUERYNO {number}"

QUERYNO_FIRST = 254
QUERYNO_STEP = 1
QUERYNO_FIRST_ORDER = 1
QUERYNO_BASE = QUERYNO_FIRST - (QUERYNO_FIRST_ORDER * QUERYNO_STEP)

__all__ = [
    "DECLARE_ON_EXEC_SQL_LINE", "DECLARE_LINE_TEMPLATE",
    "SELECT_FIRST_TEMPLATE", "SELECT_NEXT_TEMPLATE", "FROM_TEMPLATE",
    "WHERE_FIRST_TEMPLATE", "WHERE_NEXT_TEMPLATE", "ORDER_BY_TEMPLATE",
    "FOR_READ_ONLY", "END_EXEC", "LAST_DECLARATION_TERMINATOR",
    "EMIT_QUERYNO", "QUERYNO_TEMPLATE", "QUERYNO_FIRST",
    "QUERYNO_FIRST_ORDER", "QUERYNO_STEP", "QUERYNO_BASE",
]
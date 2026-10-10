# LOCATION: rules/cursor_declaration_rules.py
# ACTION: REPLACE ENTIRE FILE
"""DB2 cursor DECLARE statement rules - single import point.

REFACTOR - one 330-line constants file became six subject modules:

    cursor_declaration_geometry.py    columns, indents, widths
    cursor_declaration_templates.py   clause text, QUERYNO
    cursor_declaration_where.py       WHERE policy, operand vocabulary
    cursor_declaration_order_by.py    ORDER BY policy and labels
    cursor_declaration_warnings.py    the DB2 WARNING blocks
    cursor_declaration_messages.py    the four diagnostic catalogues

Every existing `from rules.cursor_declaration_rules import X` keeps
working. New code may import the subject module directly.

This module DECLARES NOTHING of its own. A constant defined here would
be a seventh place to look, and the duplicate-assignment defect this
file has suffered twice starts exactly that way. The only statements
below are imports and one __all__.

NON_COLUMN_SENTINELS is owned by the record materialisation rules and
re-exported, never re-declared: a second copy diverges the day one of
them gains a new sentinel. It is named in __all__ so an import cleanup
cannot remove what the declare package imports from here.

rules/db2_infrastructure_rules.py re-exports the QUERYNO names FROM
here and assigns nothing. That direction must not reverse.
"""

from __future__ import annotations

from rules.cursor_declaration_geometry import (  # noqa: F401
    BODY_FIRST_COLUMN,
    BODY_LAST_COLUMN,
    COLUMN_CLAUSE,
    COLUMN_EXEC,
    COLUMN_QUERYNO,
    COLUMN_SELECT_NEXT,
    COLUMN_WHERE_NEXT,
    IND_CLAUSE,
    IND_EXEC,
    IND_QUERYNO,
    IND_SELECT_FIRST,
    IND_SELECT_NEXT,
    IND_WHERE_NEXT,
    WARNING_BODY_WIDTH,
)
from rules.cursor_declaration_messages import (  # noqa: F401
    CURSOR_ORDER_BY_MESSAGES,
    DECLARATION_MESSAGES,
    JOIN_MESSAGES,
    ORDER_BY_KEY_MESSAGES,
    SWEEP_CURSOR_NO_WHERE_TEMPLATE,
)
from rules.cursor_declaration_order_by import (  # noqa: F401
    CHILD_CURSOR_KEEPS_ORDER_BY,
    ENFORCE_ORDER_BY_COLUMN_OWNERSHIP,
    ENFORCE_ORDER_BY_DEDUPLICATION,
    ENFORCE_ORDER_BY_RETENTION,
    ORDER_BY_DEFAULT_DIRECTION,
    ORDER_BY_DIRECTIONS,
    ORDER_BY_NARROWING_APPLIES_TO_CHILD,
    ORDER_BY_PREFER_IDENTITY_KEY,
    ORDER_BY_SOURCE_CHILD_KEY,
    ORDER_BY_SOURCE_PARENT_INTENT,
    ORDER_BY_SOURCE_PRIMARY_KEY,
    PARENT_CURSOR_KEEPS_ORDER_BY,
)
from rules.cursor_declaration_templates import (  # noqa: F401
    DECLARE_LINE_TEMPLATE,
    DECLARE_ON_EXEC_SQL_LINE,
    EMIT_QUERYNO,
    END_EXEC,
    FOR_READ_ONLY,
    FROM_TEMPLATE,
    LAST_DECLARATION_TERMINATOR,
    ORDER_BY_TEMPLATE,
    QUERYNO_BASE,
    QUERYNO_FIRST,
    QUERYNO_FIRST_ORDER,
    QUERYNO_STEP,
    QUERYNO_TEMPLATE,
    SELECT_FIRST_TEMPLATE,
    SELECT_NEXT_TEMPLATE,
    WHERE_FIRST_TEMPLATE,
    WHERE_NEXT_TEMPLATE,
)
from rules.cursor_declaration_warnings import (  # noqa: F401
    CURSOR_NOT_DECLARED_TEMPLATE,
    MISSING_COLUMNS_LINES,
    MISSING_COLUMNS_TEMPLATE,
    NO_TABLE_LABEL,
    UNRESOLVED_JOIN_KEY_LINES,
    UNRESOLVED_JOIN_KEY_TEMPLATE,
    WARNING_PREFIX,
)
from rules.cursor_declaration_where import (  # noqa: F401
    CHILD_JOIN_PREDICATE_TEMPLATE,
    DRIVING_KEY_PREDICATE_TEMPLATE,
    EMIT_DRIVING_KEY_PREDICATE,
    ENFORCE_WHERE_COLUMN_OWNERSHIP,
    HOST_VARIABLE_PREFIX,
    KEYWORD_OPERATORS,
    OPERAND_QUALIFIER_SEPARATOR,
    OPERAND_TRIM_CHARACTERS,
    SYMBOL_OPERATORS,
)
from rules.record_materialisation_rules import (  # noqa: F401
    NON_COLUMN_SENTINELS,
)

__all__ = [
    # ---- re-export from another rules module
    "NON_COLUMN_SENTINELS",
    # ---- geometry
    "BODY_FIRST_COLUMN",
    "BODY_LAST_COLUMN",
    "WARNING_BODY_WIDTH",
    "COLUMN_EXEC",
    "COLUMN_CLAUSE",
    "COLUMN_SELECT_NEXT",
    "COLUMN_WHERE_NEXT",
    "COLUMN_QUERYNO",
    "IND_EXEC",
    "IND_CLAUSE",
    "IND_SELECT_FIRST",
    "IND_SELECT_NEXT",
    "IND_WHERE_NEXT",
    "IND_QUERYNO",
    # ---- statement form
    "DECLARE_ON_EXEC_SQL_LINE",
    "DECLARE_LINE_TEMPLATE",
    "SELECT_FIRST_TEMPLATE",
    "SELECT_NEXT_TEMPLATE",
    "FROM_TEMPLATE",
    "WHERE_FIRST_TEMPLATE",
    "WHERE_NEXT_TEMPLATE",
    "ORDER_BY_TEMPLATE",
    "FOR_READ_ONLY",
    "END_EXEC",
    "LAST_DECLARATION_TERMINATOR",
    # ---- queryno
    "EMIT_QUERYNO",
    "QUERYNO_TEMPLATE",
    "QUERYNO_FIRST",
    "QUERYNO_FIRST_ORDER",
    "QUERYNO_STEP",
    "QUERYNO_BASE",
    # ---- order by
    "PARENT_CURSOR_KEEPS_ORDER_BY",
    "CHILD_CURSOR_KEEPS_ORDER_BY",
    "ENFORCE_ORDER_BY_RETENTION",
    "ENFORCE_ORDER_BY_COLUMN_OWNERSHIP",
    "ENFORCE_ORDER_BY_DEDUPLICATION",
    "ORDER_BY_DIRECTIONS",
    "ORDER_BY_DEFAULT_DIRECTION",
    "ORDER_BY_PREFER_IDENTITY_KEY",
    "ORDER_BY_NARROWING_APPLIES_TO_CHILD",
    "ORDER_BY_SOURCE_PRIMARY_KEY",
    "ORDER_BY_SOURCE_PARENT_INTENT",
    "ORDER_BY_SOURCE_CHILD_KEY",
    # ---- where
    "ENFORCE_WHERE_COLUMN_OWNERSHIP",
    "CHILD_JOIN_PREDICATE_TEMPLATE",
    "EMIT_DRIVING_KEY_PREDICATE",
    "DRIVING_KEY_PREDICATE_TEMPLATE",
    # ---- operand parsing
    "SYMBOL_OPERATORS",
    "KEYWORD_OPERATORS",
    "OPERAND_QUALIFIER_SEPARATOR",
    "HOST_VARIABLE_PREFIX",
    "OPERAND_TRIM_CHARACTERS",
    # ---- warnings
    "WARNING_PREFIX",
    "NO_TABLE_LABEL",
    "CURSOR_NOT_DECLARED_TEMPLATE",
    "UNRESOLVED_JOIN_KEY_LINES",
    "MISSING_COLUMNS_LINES",
    "UNRESOLVED_JOIN_KEY_TEMPLATE",
    "MISSING_COLUMNS_TEMPLATE",
    # ---- diagnostics
    "DECLARATION_MESSAGES",
    "SWEEP_CURSOR_NO_WHERE_TEMPLATE",
    "JOIN_MESSAGES",
    "CURSOR_ORDER_BY_MESSAGES",
    "ORDER_BY_KEY_MESSAGES",
]
# LOCATION: rules/cursor_declaration_where.py
# ACTION: CREATE NEW FILE
"""WHERE qualification policy and the operand-parsing vocabulary.

CORRECTION 6 - one predicate shape carried two constant names.

CHILD_JOIN_PREDICATE_TEMPLATE and DRIVING_KEY_PREDICATE_TEMPLATE held
the SAME literal - one edit away from a silent divergence between the
relationship path and the driving-key fallback, two predicate shapes in
one WHERE clause for no stated reason. The fallback is DERIVED from the
join template. Separate NAMES because the call sites are separate
decisions; no longer separate VALUES.

CORRECTION 12 - SQL literals lived in the builder.

SYMBOL_OPERATORS, the qualifier separator, the host prefix and the
operand trim set were module constants inside
cursor_declare_builder.py. They are SQL facts rather than site policy,
but they are LITERALS and this is where literals live.
"""

from __future__ import annotations

# The left operand of a child join predicate must be a column of the
# cursor's own FROM table. Anything else is SQLCODE -206 at bind.
ENFORCE_WHERE_COLUMN_OWNERSHIP = True

CHILD_JOIN_PREDICATE_TEMPLATE = "{child_column} = :{parent_group}.{parent_host}"

# A cursor with no WHERE is a root/sweep cursor. CORRECT for an IDMS
# area sweep, WRONG for a qualified access whose Sheet Mapping rows were
# never classified as FOREIGN.
#
# The fallback qualifies the CHILD column against a PARENT host. It
# never compares a column to its own group: "COL = :OWNGROUP.COL" is a
# meaningless filter, not a join.
EMIT_DRIVING_KEY_PREDICATE = True

# DERIVED, not duplicated. See CORRECTION 6.
DRIVING_KEY_PREDICATE_TEMPLATE = CHILD_JOIN_PREDICATE_TEMPLATE

# ---------------------------------------------------------------------
# Operand parsing vocabulary
# ---------------------------------------------------------------------
# Longest symbol first, so "<=" is never read as "<".
SYMBOL_OPERATORS = ("<>", "!=", ">=", "<=", "=", "<", ">")

# A predicate may use a KEYWORD operator instead of a symbol:
#
#     DA_CRFMAS_479BFAS IS NOT NULL
#     NR_ID_479BFAS BETWEEN :H1 AND :H2
#     CO_ID_479BFAS IN (:H1, :H2)
#     NM_ID_479BFAS LIKE :H1
#
# In that form there is no symbol to cut at, so the parser takes the
# FIRST operand token. This tuple documents the shapes that forced that
# design; the parser does not match against it.
KEYWORD_OPERATORS = ("IS", "LIKE", "IN", "BETWEEN", "NOT", "EXISTS")

# T.NR_ID and NR_ID are the same column; only the bare name is compared.
OPERAND_QUALIFIER_SEPARATOR = "."

# A leading colon marks a HOST VARIABLE, never a column.
HOST_VARIABLE_PREFIX = ":"

# Characters a predicate may wrap an operand in.
OPERAND_TRIM_CHARACTERS = "() \t"

__all__ = [
    "ENFORCE_WHERE_COLUMN_OWNERSHIP",
    "CHILD_JOIN_PREDICATE_TEMPLATE",
    "EMIT_DRIVING_KEY_PREDICATE",
    "DRIVING_KEY_PREDICATE_TEMPLATE",
    "SYMBOL_OPERATORS", "KEYWORD_OPERATORS",
    "OPERAND_QUALIFIER_SEPARATOR", "HOST_VARIABLE_PREFIX",
    "OPERAND_TRIM_CHARACTERS",
]
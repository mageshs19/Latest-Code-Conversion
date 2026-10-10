# LOCATION: rules/cursor_declaration_order_by.py
# ACTION: REPLACE ENTIRE FILE
from __future__ import annotations

# ORDER BY retention.
# VMDZ7200 (Train Case 3) ends its ROOT cursor with
#     ORDER BY NR_ID_479BFAS ASC
# so a parent cursor DOES order. The converter may REFUSE a clause it
# cannot resolve; it must never DELETE one that has been resolved.
PARENT_CURSOR_KEEPS_ORDER_BY = True
CHILD_CURSOR_KEEPS_ORDER_BY = True

# Master switch. False only to reproduce pre-correction output.
ENFORCE_ORDER_BY_RETENTION = True

# The COLUMN part of an entry must be a real column of the cursor's own
# FROM table. A generated declaration once carried ", FILLER" - a COBOL
# placeholder, not a DB2 column - which binds as SQLCODE -206.
ENFORCE_ORDER_BY_COLUMN_OWNERSHIP = True

# After the direction suffix is stripped, "NR_ID ASC" and "NR_ID DESC"
# are ONE column with contradictory directions. DB2 rejects that.
ENFORCE_ORDER_BY_DEDUPLICATION = True

ORDER_BY_DIRECTIONS = ("ASC", "DESC")

# DERIVED: a default outside the allowed set is unrenderable.
ORDER_BY_DEFAULT_DIRECTION = ORDER_BY_DIRECTIONS[0]

# Narrow to the identity key WHEN ONE EXISTS. A surrogate key is unique
# on its own, so a wider composite adds sort cost and no determinism.
ORDER_BY_PREFER_IDENTITY_KEY = True

# A child cursor is already qualified by the parent key in WHERE, so the
# identity key alone remains a total order inside the result set.
ORDER_BY_NARROWING_APPLIES_TO_CHILD = True

# Feed the {source} field of CURSOR_ORDER_BY_MESSAGES["resolved"].
ORDER_BY_SOURCE_PRIMARY_KEY = "Sheet Mapping primary key"
ORDER_BY_SOURCE_PARENT_INTENT = "Sheet Mapping order semantics"
ORDER_BY_SOURCE_CHILD_KEY = "relationship key"

__all__ = [
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
]
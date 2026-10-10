# LOCATION: converter/generators/db2_infrastructure/cursor_declare/declare_clause_renderer.py
# ACTION: CREATE NEW FILE
"""Renders the clauses of one DECLARE, in SQL order.

    SELECT, FROM, WHERE, ORDER BY, FOR READ ONLY, QUERYNO

QUERYNO is LAST inside the statement, immediately before END-EXEC, so
DB2 EXPLAIN can tie an access path back to the cursor.

Owns no decision: it is handed the final column, predicate and ORDER BY
lists and lays them out.
"""

from __future__ import annotations

from rules.cursor_declaration_rules import (
    EMIT_QUERYNO,
    QUERYNO_BASE,
    QUERYNO_STEP,
    QUERYNO_TEMPLATE,
)
from rules.db2_infrastructure_rules import (
    DECLARE_TEMPLATE,
    FROM_TEMPLATE,
    IND_EXEC,
    IND_SELECT_FIRST,
    IND_SELECT_NEXT,
    IND_SQL_BODY,
    IND_WHERE_NEXT,
    SELECT_ITEM_FIRST_TEMPLATE,
    SELECT_ITEM_NEXT_TEMPLATE,
    TOKEN_END_EXEC,
    TOKEN_EXEC_SQL,
    TOKEN_FOR_READ_ONLY,
    TOKEN_ORDER_BY,
    TOKEN_SELECT,
    TOKEN_WHERE,
)

NO_QUERYNO = 0


class DeclareClauseRenderer:
    """Lays out one DECLARE CURSOR statement."""

    def __init__(self, line_utils) -> None:
        self.line_utils = line_utils

    def render(
        self,
        spec,
        columns: list[str],
        conditions: list[str],
        order_by: list[str],
    ) -> list[str]:
        lines: list[str] = [
            f"{IND_EXEC}{TOKEN_EXEC_SQL}",
            f"{IND_SQL_BODY}"
            f"{DECLARE_TEMPLATE.format(cursor=spec.cursor_name)}",
            f"{IND_SQL_BODY}{TOKEN_SELECT}",
        ]
        lines.extend(self.select_lines(columns))
        lines.append(
            f"{IND_SQL_BODY}{FROM_TEMPLATE.format(table=spec.table_name)}"
        )
        lines.extend(self.where_lines(conditions))
        lines.extend(self.order_by_lines(order_by))
        lines.append(f"{IND_SQL_BODY}{TOKEN_FOR_READ_ONLY}")
        lines.extend(self.queryno_lines(spec.cursor_order))
        lines.append(f"{IND_EXEC}{TOKEN_END_EXEC}")
        return lines

    @staticmethod
    def select_lines(columns: list[str]) -> list[str]:
        """Comma-leading list, so the column names line up."""
        out: list[str] = []
        for index, column in enumerate(columns or []):
            template = (
                SELECT_ITEM_FIRST_TEMPLATE if index == 0
                else SELECT_ITEM_NEXT_TEMPLATE
            )
            indent = IND_SELECT_FIRST if index == 0 else IND_SELECT_NEXT
            out.append(indent + template.format(column=column))
        return out

    def where_lines(self, conditions: list[str]) -> list[str]:
        if not conditions:
            return []
        return [
            f"{IND_SQL_BODY}{TOKEN_WHERE}",
            *self.line_utils.and_lines(
                items=conditions,
                indent=IND_WHERE_NEXT,
            ),
        ]

    def order_by_lines(self, columns: list[str]) -> list[str]:
        """ORDER BY clause.

        IND_WHERE_NEXT is DELIBERATE, not a copy-paste slip: the manual
        reference indents a WHERE predicate and an ORDER BY entry to the
        SAME column. The constant is named for the clause that first
        needed it; it is the shared continuation indent.
        """
        if not columns:
            return []
        return [
            f"{IND_SQL_BODY}{TOKEN_ORDER_BY}",
            *self.line_utils.comma_lines(
                items=columns,
                indent=IND_WHERE_NEXT,
            ),
        ]

    @classmethod
    def queryno_lines(cls, cursor_order: int) -> list[str]:
        if not EMIT_QUERYNO:
            return []
        number = cls.queryno(cursor_order)
        return [f"{IND_SQL_BODY}{QUERYNO_TEMPLATE.format(number=number)}"]

    @staticmethod
    def queryno(cursor_order: int) -> int:
        """DERIVED, never hardcoded, so repeated runs are byte-identical
        and two cursors in one program can never collide."""
        if not EMIT_QUERYNO:
            return NO_QUERYNO
        return QUERYNO_BASE + (int(cursor_order or 0) * QUERYNO_STEP)


__all__ = ["DeclareClauseRenderer", "NO_QUERYNO"]
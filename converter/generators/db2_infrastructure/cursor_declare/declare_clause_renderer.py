# LOCATION: converter/generators/db2_infrastructure/cursor_declare/declare_clause_renderer.py
# ACTION: REPLACE ENTIRE FILE
"""Renders the clauses of one DECLARE, in SQL order.

    SELECT, FROM, WHERE, ORDER BY, FOR READ ONLY, QUERYNO

QUERYNO is LAST inside the statement, immediately before END-EXEC, so
DB2 EXPLAIN can tie an access path back to the cursor.

Owns no decision: it is handed the final column, predicate and ORDER BY
lists and lays them out.

CORRECTION 1 - the statement opened on TWO lines.

    EXEC SQL
      DECLARE DZBEFFC1 CURSOR WITH HOLD FOR

The manual reference opens on ONE:

    EXEC SQL DECLARE DZBEFFC1 CURSOR WITH HOLD FOR

rules/cursor_declaration_templates.py already carried the decision and
the template, and said so in a comment:

    # True -> EXEC SQL DECLARE <cursor> CURSOR WITH HOLD FOR (manual)
    DECLARE_ON_EXEC_SQL_LINE = True

This renderer never read either name. It now does, and the two-line form
is still reachable by setting the flag False.

CORRECTION 2 - SELECT, WHERE and ORDER BY stood alone on their line.

    SELECT
      AM_CNDSTK_479BEFF
    , AM_CNSTK_479BEFF

The manual carries the FIRST item on the keyword line and aligns every
continuation under it:

    SELECT CO_IDPRKSK_479BEFF
         , NS_IRMOSTK_479BEFF

Continuation indents are DERIVED from the keyword width, not typed as a
constant, so they cannot drift out of alignment when IND_SQL_BODY moves.
IND_SELECT_FIRST and IND_SELECT_NEXT are consequently no longer read by
this module.

CORRECTION 3 - every declaration closed with a period.

    "Every declaration except the last closes with a bare END-EXEC. The
     last one closes the WORKING-STORAGE sentence with a period."

Both generated declarations carried "END-EXEC.". render() now takes
is_last. It DEFAULTS TO TRUE, so a caller that does not pass it produces
exactly the previous bytes; CursorDeclareBuilder must pass is_last=False
for every declaration but the final one to get the manual shape.

CLAUSE WIDTH is not checked here. A predicate wide enough to pass column
72 is handed on intact for the fixed-format service to wrap. Truncating
a predicate would change the result set in silence.
"""

from __future__ import annotations

# Manual-reference STATEMENT SHAPE. These names are owned by
# rules/cursor_declaration_templates.py and re-exported here.
from rules.cursor_declaration_rules import (
    DECLARE_LINE_TEMPLATE,
    DECLARE_ON_EXEC_SQL_LINE,
    EMIT_QUERYNO,
    END_EXEC,
    LAST_DECLARATION_TERMINATOR,
    QUERYNO_BASE,
    QUERYNO_STEP,
    QUERYNO_TEMPLATE,
    SELECT_FIRST_TEMPLATE,
    SELECT_NEXT_TEMPLATE,
    WHERE_FIRST_TEMPLATE,
    WHERE_NEXT_TEMPLATE,
)

# GEOMETRY and TOKENS for the live builder.
from rules.db2_infrastructure_rules import (
    DECLARE_TEMPLATE,
    FROM_TEMPLATE,
    IND_EXEC,
    IND_SQL_BODY,
    IND_WHERE_NEXT,
    TOKEN_END_EXEC,
    TOKEN_EXEC_SQL,
    TOKEN_FOR_READ_ONLY,
    TOKEN_ORDER_BY,
    TOKEN_SELECT,
    TOKEN_WHERE,
)

NO_QUERYNO = 0

# A continuation carries ", " where the first line carried "<KEYWORD> ".
# Deriving the difference keeps the operands in one column whatever
# IND_SQL_BODY becomes.
_SEPARATOR_WIDTH = len(", ")


def _continuation_indent(keyword: str) -> str:
    """Indent that lines a continued item up under the first one."""
    width = len(IND_SQL_BODY) + len(keyword) + 1 - _SEPARATOR_WIDTH
    return " " * max(width, len(IND_SQL_BODY))


IND_SELECT_CONTINUATION = _continuation_indent(TOKEN_SELECT)
IND_ORDER_BY_CONTINUATION = _continuation_indent(TOKEN_ORDER_BY)


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
        is_last: bool = True,
    ) -> list[str]:
        lines: list[str] = self.open_lines(spec.cursor_name)
        lines.extend(self.select_lines(columns))
        lines.append(
            f"{IND_SQL_BODY}{FROM_TEMPLATE.format(table=spec.table_name)}"
        )
        lines.extend(self.where_lines(conditions))
        lines.extend(self.order_by_lines(order_by))
        lines.append(f"{IND_SQL_BODY}{TOKEN_FOR_READ_ONLY}")
        lines.extend(self.queryno_lines(spec.cursor_order))
        lines.append(self.close_line(is_last))
        return lines

    # ---- statement open
    @staticmethod
    def open_lines(cursor_name: str) -> list[str]:
        """One line in the manual form, two when the flag is False."""
        if DECLARE_ON_EXEC_SQL_LINE:
            return [
                f"{IND_EXEC}"
                f"{DECLARE_LINE_TEMPLATE.format(cursor=cursor_name)}"
            ]

        return [
            f"{IND_EXEC}{TOKEN_EXEC_SQL}",
            f"{IND_SQL_BODY}{DECLARE_TEMPLATE.format(cursor=cursor_name)}",
        ]

    # ---- statement close
    @staticmethod
    def close_line(is_last: bool = True) -> str:
        """Bare END-EXEC, except on the declaration that ends the sentence."""
        if is_last:
            return f"{IND_EXEC}{TOKEN_END_EXEC}"
        return f"{IND_EXEC}{END_EXEC}"

    # ---- SELECT
    @staticmethod
    def select_lines(columns: list[str]) -> list[str]:
        """First column on the SELECT line, the rest comma-leading.

        An empty list still emits the bare keyword so a malformed
        statement is visible rather than missing a clause. The builder
        refuses an empty column list upstream (D-6), so this is a guard,
        not a path.
        """
        if not columns:
            return [f"{IND_SQL_BODY}{TOKEN_SELECT}"]

        out: list[str] = [
            f"{IND_SQL_BODY}"
            f"{SELECT_FIRST_TEMPLATE.format(column=columns[0])}"
        ]
        out.extend(
            f"{IND_SELECT_CONTINUATION}"
            f"{SELECT_NEXT_TEMPLATE.format(column=column)}"
            for column in columns[1:]
        )
        return out

    # ---- WHERE
    def where_lines(self, conditions: list[str]) -> list[str]:
        """First predicate on the WHERE line, the rest AND-leading."""
        if not conditions:
            return []

        out: list[str] = [
            f"{IND_SQL_BODY}"
            f"{WHERE_FIRST_TEMPLATE.format(condition=conditions[0])}"
        ]
        out.extend(
            f"{IND_WHERE_NEXT}"
            f"{WHERE_NEXT_TEMPLATE.format(condition=condition)}"
            for condition in conditions[1:]
        )
        return out

    # ---- ORDER BY
    def order_by_lines(self, columns: list[str]) -> list[str]:
        """First entry on the ORDER BY line, the rest comma-leading.

        A single-column clause therefore renders as one line, which is
        the manual reference shape:

            ORDER BY NR_ID_479EVEF DESC
        """
        if not columns:
            return []

        out: list[str] = [f"{IND_SQL_BODY}{TOKEN_ORDER_BY} {columns[0]}"]
        out.extend(
            f"{IND_ORDER_BY_CONTINUATION}, {column}"
            for column in columns[1:]
        )
        return out

    # ---- QUERYNO
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


__all__ = [
    "DeclareClauseRenderer",
    "NO_QUERYNO",
    "IND_SELECT_CONTINUATION",
    "IND_ORDER_BY_CONTINUATION",
]
# LOCATION: converter/generators/cursor_declaration/legacy_clause_renderer.py
# ACTION: CREATE NEW FILE
"""The LEGACY clause shape: 'SELECT <column>' on one line.

    EXEC SQL DECLARE DZBEFFC1 CURSOR WITH HOLD FOR
      SELECT CO_IDPRKSK_479BEFF
           , NS_IRMOSTK_479BEFF
      FROM DZBEFFTV
     WHERE CT_RKTPROD_479BEFF = :DCLDZBEFFTV.CT-RKTPROD-479BEFF
       AND NR_IDSTOCK_479BEFF = :DCLDZBEFFTV.NR-IDSTOCK-479BEFF
      FOR READ ONLY
             QUERYNO 254
    END-EXEC

It differs from DeclareClauseRenderer in exactly two ways:

  - the keyword and its first item share a line (SELECT_FIRST_TEMPLATE
    carries the keyword), where the new shape puts the keyword alone;
  - ORDER BY renders as one space-joined line rather than a comma list.

Everything else - what to select, what to filter on, what survives in
ORDER BY - is decided elsewhere and handed in.
"""

from __future__ import annotations

from rules.cursor_declaration_legacy import IND_WHERE_FIRST
from rules.cursor_declaration_rules import (
    DECLARE_LINE_TEMPLATE,
    DECLARE_ON_EXEC_SQL_LINE,
    EMIT_QUERYNO,
    END_EXEC,
    FOR_READ_ONLY,
    FROM_TEMPLATE,
    IND_CLAUSE,
    IND_EXEC,
    IND_QUERYNO,
    IND_SELECT_FIRST,
    IND_SELECT_NEXT,
    IND_WHERE_NEXT,
    LAST_DECLARATION_TERMINATOR,
    ORDER_BY_TEMPLATE,
    QUERYNO_BASE,
    QUERYNO_STEP,
    QUERYNO_TEMPLATE,
    SELECT_FIRST_TEMPLATE,
    SELECT_NEXT_TEMPLATE,
    WHERE_FIRST_TEMPLATE,
    WHERE_NEXT_TEMPLATE,
)

ORDER_BY_JOIN = " "
NO_TERMINATOR = ""


class LegacyClauseRenderer:
    """Lays out one legacy DECLARE CURSOR statement."""

    def render(
        self,
        cursor: str,
        table: str,
        columns: list[str],
        conditions: list[str],
        order_by: list[str],
        cursor_order: int,
        is_last: bool,
    ) -> list[str]:
        lines: list[str] = []
        lines.extend(self._declare(cursor))
        lines.extend(self._select(columns))
        lines.append(f"{IND_CLAUSE}{FROM_TEMPLATE.format(table=table)}")
        lines.extend(self._where(conditions))
        lines.extend(self._order_by(order_by))
        lines.append(f"{IND_CLAUSE}{FOR_READ_ONLY}")
        lines.extend(self._queryno(cursor_order))
        lines.append(self._end_exec(is_last))
        return lines

    # ---- clauses
    @staticmethod
    def _declare(cursor: str) -> list[str]:
        if DECLARE_ON_EXEC_SQL_LINE:
            return [f"{IND_EXEC}{DECLARE_LINE_TEMPLATE.format(cursor=cursor)}"]
        return [
            f"{IND_EXEC}EXEC SQL",
            f"{IND_CLAUSE}{DECLARE_LINE_TEMPLATE.format(cursor=cursor)}",
        ]

    @staticmethod
    def _select(columns: list[str]) -> list[str]:
        out: list[str] = []
        for position, column in enumerate(columns or []):
            if position == 0:
                out.append(
                    IND_SELECT_FIRST
                    + SELECT_FIRST_TEMPLATE.format(column=column)
                )
            else:
                out.append(
                    IND_SELECT_NEXT
                    + SELECT_NEXT_TEMPLATE.format(column=column)
                )
        return out

    @staticmethod
    def _where(conditions: list[str]) -> list[str]:
        out: list[str] = []
        for position, condition in enumerate(conditions or []):
            if position == 0:
                out.append(
                    IND_WHERE_FIRST
                    + WHERE_FIRST_TEMPLATE.format(condition=condition)
                )
            else:
                out.append(
                    IND_WHERE_NEXT
                    + WHERE_NEXT_TEMPLATE.format(condition=condition)
                )
        return out

    @staticmethod
    def _order_by(columns: list[str]) -> list[str]:
        if not columns:
            return []
        joined = ORDER_BY_JOIN.join(columns)
        return [f"{IND_CLAUSE}{ORDER_BY_TEMPLATE.format(columns=joined)}"]

    @classmethod
    def _queryno(cls, cursor_order: int) -> list[str]:
        if not EMIT_QUERYNO:
            return []
        number = cls.queryno(cursor_order)
        return [f"{IND_QUERYNO}{QUERYNO_TEMPLATE.format(number=number)}"]

    @staticmethod
    def queryno(cursor_order: int) -> int:
        """1-BASED, matching CursorDeclareBuilder. See CORRECTION 3."""
        if not EMIT_QUERYNO:
            return 0
        return QUERYNO_BASE + (int(cursor_order or 0) * QUERYNO_STEP)

    @staticmethod
    def _end_exec(is_last: bool) -> str:
        terminator = LAST_DECLARATION_TERMINATOR if is_last else NO_TERMINATOR
        return f"{IND_EXEC}{END_EXEC}{terminator}"


__all__ = ["LegacyClauseRenderer"]
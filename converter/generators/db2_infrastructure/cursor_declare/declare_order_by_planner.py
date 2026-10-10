# LOCATION: converter/generators/db2_infrastructure/cursor_declare/declare_order_by_planner.py
# ACTION: CREATE NEW FILE
"""Decides which ORDER BY entries survive into the declaration.

GOVERNING RULE: the converter may REFUSE to generate a clause it cannot
resolve. It must never DELETE one that has been resolved.

A generated declaration once carried

    ORDER BY CT_RKTGDSV_479BFAS
           , FILLER            <- COBOL placeholder
           , NR_ID_479BFAS DESC

FILLER is not a DB2 column, so the DECLARE bound as SQLCODE -206 and
the program never ran. One bad entry never loses the whole ordering.

CORRECTION - a duplicate was reported with the WRONG REASON.

The dedup pass logged "order_by_column_dropped", whose text reads
"... is not a column of {table}". The column IS a column of that table;
it is simply already ordered. A diagnostic that states a false cause
sends the reader to the DCLGEN instead of the ORDER BY resolver.

CORRECTION - ENFORCE_ORDER_BY_DEDUPLICATION existed and nothing read
it, the same defect class that left ENFORCE_WHERE_COLUMN_OWNERSHIP
unreachable.
"""

from __future__ import annotations

from converter.generators.db2_infrastructure.cursor_declare.declare_diagnostics import (
    DeclareDiagnostics,
)
from converter.generators.db2_infrastructure.cursor_declare.declare_operand_parser import (
    DeclareOperandParser,
)
from rules.cursor_declaration_rules import (
    CHILD_CURSOR_KEEPS_ORDER_BY,
    ENFORCE_ORDER_BY_COLUMN_OWNERSHIP,
    ENFORCE_ORDER_BY_DEDUPLICATION,
    ENFORCE_ORDER_BY_RETENTION,
    NON_COLUMN_SENTINELS,
    PARENT_CURSOR_KEEPS_ORDER_BY,
)


class DeclareOrderByPlanner:
    """Filters the resolved ORDER BY entries of one cursor."""

    def __init__(self, diagnostics: DeclareDiagnostics) -> None:
        self.diagnostics = diagnostics

    def plan(self, spec, has_where: bool, owned: set[str]) -> list[str]:
        entries = [
            str(column or "").strip()
            for column in list(spec.order_by_columns or [])
            if str(column or "").strip()
        ]

        if not entries:
            self.diagnostics.log("order_by_none", cursor=spec.cursor_name)
            return []

        if ENFORCE_ORDER_BY_DEDUPLICATION:
            entries = self._deduplicated(entries, spec)

        if ENFORCE_ORDER_BY_COLUMN_OWNERSHIP:
            entries = self._owned(entries, spec, owned)

        if not entries:
            self.diagnostics.log("order_by_all_dropped", cursor=spec.cursor_name)
            return []

        if not ENFORCE_ORDER_BY_RETENTION and not self._legacy_keep(has_where):
            self.diagnostics.log("order_by_removed", cursor=spec.cursor_name)
            return []

        self.diagnostics.log(
            "order_by_kept",
            cursor=spec.cursor_name,
            count=len(entries),
        )
        return entries

    # ---- passes
    def _deduplicated(self, entries: list[str], spec) -> list[str]:
        """First entry for a column wins.

        'NR_ID ASC' and 'NR_ID DESC' are one column carrying
        contradictory directions; DB2 rejects the statement.
        """
        kept: list[str] = []
        seen: set[str] = set()

        for entry in entries:
            key = DeclareOperandParser.order_by_column(entry).upper()

            # Unparseable: leave it for the ownership pass to judge.
            if not key:
                kept.append(entry)
                continue

            if key in seen:
                self.diagnostics.log(
                    "order_by_duplicate_dropped",
                    entry=entry,
                    cursor=spec.cursor_name,
                    column=key,
                    table=spec.table_name,
                )
                continue

            seen.add(key)
            kept.append(entry)

        return kept

    def _owned(self, entries: list[str], spec, owned: set[str]) -> list[str]:
        """Keep only entries whose COLUMN belongs to the FROM table.

        A sentinel is dropped even with no column list, because it can
        never be a DB2 column. Ownership itself stands down without a
        column list, so a thin DCLGEN never costs a valid ordering.
        """
        sentinels = {
            str(name or "").strip().upper()
            for name in (NON_COLUMN_SENTINELS or ())
        }

        kept: list[str] = []

        for entry in entries:
            column = DeclareOperandParser.order_by_column(entry)
            token = column.upper()

            unreadable = not column or token in sentinels
            unowned = bool(owned) and token not in owned

            if unreadable or unowned:
                self.diagnostics.log(
                    "order_by_column_dropped",
                    entry=entry,
                    cursor=spec.cursor_name,
                    column=column or entry,
                    table=spec.table_name,
                )
                continue

            kept.append(entry)

        return kept

    @staticmethod
    def _legacy_keep(has_where: bool) -> bool:
        """Reachable only when retention is off for a deliberate diff."""
        return (
            CHILD_CURSOR_KEEPS_ORDER_BY
            if has_where
            else PARENT_CURSOR_KEEPS_ORDER_BY
        )


__all__ = ["DeclareOrderByPlanner"]
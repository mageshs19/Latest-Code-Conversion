# LOCATION: converter/generators/db2_infrastructure/cursor_declare/declare_column_ownership.py
# ACTION: REPLACE ENTIRE FILE
"""Which columns does a table own, and is this predicate legal?

ONE lookup serves both the WHERE guard and the ORDER BY guard. Two
copies of one fact drift: the WHERE copy once had no sentinel filtering
while the ORDER BY copy did.

An empty set means CANNOT VALIDATE, never APPROVED. Every route to that
outcome is reported ONCE per table - a silent stand-down hides the gap,
a repeated one buries it in noise.
"""

from __future__ import annotations

from converter.generators.db2_infrastructure.cursor_declare.declare_diagnostics import (
    DeclareDiagnostics,
)
from converter.generators.db2_infrastructure.cursor_declare.declare_operand_parser import (
    DeclareOperandParser,
)
from rules.cursor_declaration_rules import NO_TABLE_LABEL


class DeclareColumnOwnership:
    """Per-table column lookup with a real cache."""

    def __init__(
        self,
        diagnostics: DeclareDiagnostics,
        column_name_resolver=None,
    ) -> None:
        self.diagnostics = diagnostics
        self.column_name_resolver = column_name_resolver

        # table -> owned columns. A program commonly declares several
        # cursors on one table; without this the resolver was called
        # once per cursor and the stand-down message repeated verbatim.
        self._cache: dict[str, set[str]] = {}

    def reset(self) -> None:
        """A new program may carry a different DCLGEN."""
        self._cache = {}

    def columns_of(self, table: str) -> set[str]:
        """Uppercased DB2 column names of `table`, or an empty set."""
        if not table:
            self.diagnostics.log("ownership_unavailable", table=NO_TABLE_LABEL)
            return set()

        key = str(table).strip().upper()
        if key in self._cache:
            return self._cache[key]

        owned = self._resolve(table)
        self._cache[key] = owned
        return owned

    def first_unowned(self, conditions: list[str], owned: set[str]) -> str:
        """First WHERE left operand not owned by the cursor's table.

        A child cursor may only filter on columns of its own FROM table;
        a parent column on the left is SQLCODE -206 at bind time.
        Returns "" when every predicate is valid, or when no column list
        is available - the stand-down is already reported.
        """
        if not conditions or not owned:
            return ""

        for condition in conditions:
            left = DeclareOperandParser.left_operand(condition)
            if left and left.upper() not in owned:
                return left

        return ""

    # ---- one resolver call per table
    def _resolve(self, table: str) -> set[str]:
        if self.column_name_resolver is None:
            self.diagnostics.log("ownership_no_resolver", table=table)
            return set()

        try:
            columns = self.column_name_resolver.columns_for_table(table)
        except Exception as exc:  # noqa: BLE001 - reported, not swallowed
            self.diagnostics.log(
                "ownership_lookup_failed",
                table=table,
                reason=f"{type(exc).__name__}: {exc}",
            )
            return set()

        owned = {
            str(column or "").strip().upper()
            for column in (columns or [])
            if str(column or "").strip()
        }

        if not owned:
            self.diagnostics.log("ownership_unavailable", table=table)

        return owned


__all__ = ["DeclareColumnOwnership"]
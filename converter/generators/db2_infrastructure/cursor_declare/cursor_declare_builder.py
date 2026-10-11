# LOCATION: converter/generators/db2_infrastructure/cursor_declare/cursor_declare_builder.py
# ACTION: CREATE NEW FILE
"""Renders one DECLARE CURSOR statement.

Clause order is fixed by SQL and by the manual reference:

    SELECT, FROM, WHERE, ORDER BY, FOR READ ONLY, QUERYNO

REFACTOR - one 600-line class became five collaborators:

    declare_diagnostics.py       the decision record
    declare_operand_parser.py    column out of a free-text fragment
    declare_column_ownership.py  what does this table own
    declare_order_by_planner.py  which ORDER BY entries survive
    declare_clause_renderer.py   layout
    declare_refusal.py           the DB2 WARNING blocks

build() now reads as the sequence of decisions it is. The seventeen
corrections this file accumulated live beside the code each one fixed,
so a reader of the ORDER BY planner sees the ORDER BY history and
nothing else.

The public surface is UNCHANGED: build(spec) -> list[str], reset(), and
a messages list.

Clean Architecture:

- Every COBOL / SQL literal lives in rules/cursor_declaration_rules.py
  and rules/db2_infrastructure_rules.py.
- No regex is defined in this package.
- No program, record, table, cursor or host variable name is hardcoded.
"""

from __future__ import annotations

from converter.generators.db2_infrastructure.cursor_declare.declare_clause_renderer import (
    DeclareClauseRenderer,
)
from converter.generators.db2_infrastructure.cursor_declare.declare_column_ownership import (
    DeclareColumnOwnership,
)
from converter.generators.db2_infrastructure.cursor_declare.declare_diagnostics import (
    DeclareDiagnostics,
)
from converter.generators.db2_infrastructure.cursor_declare.declare_order_by_planner import (
    DeclareOrderByPlanner,
)
from converter.generators.db2_infrastructure.cursor_declare.declare_refusal import (
    DeclareRefusal,
)
from converter.generators.db2_infrastructure.cursor_spec import CursorSpec
from rules.cursor_declaration_rules import (
    ENFORCE_ORDER_BY_COLUMN_OWNERSHIP,
    ENFORCE_WHERE_COLUMN_OWNERSHIP,
    SWEEP_CURSOR_NO_WHERE_TEMPLATE,
)


class CursorDeclareBuilder:
    """Renders one DECLARE CURSOR statement."""

    def __init__(
        self,
        line_utils,
        column_name_resolver=None,
    ) -> None:
        self.line_utils = line_utils
        # Optional. When absent, ownership cannot be validated. The
        # guard stands down rather than refusing a valid cursor, but
        # the stand-down is always reported.
        self.column_name_resolver = column_name_resolver

        self.diagnostics = DeclareDiagnostics()
        self.ownership = DeclareColumnOwnership(
            diagnostics=self.diagnostics,
            column_name_resolver=column_name_resolver,
        )
        self.order_by = DeclareOrderByPlanner(self.diagnostics)
        self.refusal = DeclareRefusal(self.diagnostics)
        self.renderer = DeclareClauseRenderer(line_utils)

    # ---- the message list stays a plain attribute for existing callers
    @property
    def messages(self) -> list[str]:
        return self.diagnostics.messages

    def reset(self) -> None:
        """Drop state from the previous program.

        One instance renders every cursor of every program in a folder
        run, so an uncleared report carries program 1's diagnostics into
        program 2. The ownership cache is keyed by table and a new
        program may carry a different DCLGEN, so it is cleared too.
        """
        self.diagnostics.reset()
        self.ownership.reset()

    # =================================================================
    # Public entry point
    # =================================================================
    def build(self, spec: CursorSpec, is_last: bool = True) -> list[str]:
        if not spec.cursor_name:
            return self.refusal.no_cursor_name()

        if not spec.table_name:
            return self.refusal.no_table(spec.cursor_name)

        columns = list(spec.select_columns or [])
        if not columns:
            return self.refusal.no_columns(spec.cursor_name, spec.table_name)

        conditions = self._conditions(spec)

        # ONE ownership lookup per declaration, and only when a guard
        # will actually consume it.
        owned: set[str] = set()
        if ENFORCE_WHERE_COLUMN_OWNERSHIP or ENFORCE_ORDER_BY_COLUMN_OWNERSHIP:
            owned = self.ownership.columns_of(spec.table_name)

        if ENFORCE_WHERE_COLUMN_OWNERSHIP:
            unowned = self.ownership.first_unowned(conditions, owned)
            if unowned:
                return self.refusal.unowned_join_key(
                    cursor=spec.cursor_name,
                    column=unowned,
                    table=spec.table_name,
                )

        has_where = self._report_where(spec, conditions)
        order_by = self.order_by.plan(spec, has_where, owned)

        lines = self.renderer.render(
            spec=spec,
            columns=columns,
            conditions=conditions,
            order_by=order_by,
            is_last=is_last,
        )

        self.diagnostics.log(
            "declared_cursor",
            cursor=spec.cursor_name,
            table=spec.table_name,
            count=len(columns),
            queryno=self.renderer.queryno(spec.cursor_order),
        )
        return lines

    # =================================================================
    # Helpers
    # =================================================================
    @staticmethod
    def _conditions(spec: CursorSpec) -> list[str]:
        """De-duplicated predicates, order preserved."""
        out: list[str] = []
        seen: set[str] = set()

        for condition in list(spec.where_conditions or []):
            value = str(condition or "").strip()
            if not value or value in seen:
                continue
            seen.add(value)
            out.append(value)

        return out

    def _report_where(self, spec: CursorSpec, conditions: list[str]) -> bool:
        """Record whether this cursor is qualified, and return it.

        A cursor with no WHERE is a root/sweep read. That is CORRECT for
        an IDMS area sweep and WRONG for a qualified access whose Sheet
        Mapping rows were never classified as FOREIGN, so it is always
        reported rather than assumed.
        """
        if conditions:
            self.diagnostics.log(
                "where_declared",
                cursor=spec.cursor_name,
                count=len(conditions),
            )
            return True

        self.diagnostics.add(
            SWEEP_CURSOR_NO_WHERE_TEMPLATE.format(
                cursor=spec.cursor_name,
                table=spec.table_name,
            )
        )
        return False


__all__ = ["CursorDeclareBuilder"]
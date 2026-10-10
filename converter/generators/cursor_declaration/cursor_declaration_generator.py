# LOCATION: converter/generators/cursor_declaration/cursor_declaration_generator.py
# ACTION: CREATE NEW FILE
"""Generates DB2 cursor DECLARE statements - LEGACY shape.

Emits the COBOL team's manual reference layout:

    * DECLARE CURSOR FOR BEFF TABLE
    * ------------------------------
    *
        EXEC SQL DECLARE DZBEFFC1 CURSOR WITH HOLD FOR
          SELECT CO_IDPRKSK_479BEFF
               , NS_IRMOSTK_479BEFF
          FROM DZBEFFTV
          FOR READ ONLY
                 QUERYNO 254
        END-EXEC

REFACTOR - this generator re-implemented four decisions that
CursorDeclareBuilder had already corrected, and the two had DIVERGED.
It now REUSES the shared collaborators and keeps only what is genuinely
legacy: the banner and the one-line SELECT shape.

    declare_diagnostics.py       the decision record
    declare_column_ownership.py  what does this table own
    declare_order_by_planner.py  which ORDER BY entries survive
    declare_refusal.py           the DB2 WARNING blocks
    legacy_banner_builder.py     LEGACY - the comment banner
    legacy_clause_renderer.py    LEGACY - the one-line SELECT shape

CORRECTION 1 - the warnings were re-declared here.

Three templates sat as module constants while rules/ already owned
those names, and the wording had drifted ("missing DB2 table mapping."
against "no DB2 table."). Both generators now emit the same sentence
for the same refusal.

CORRECTION 2 - the ownership guard split on '=' only.

    left = condition.split("=", 1)[0]

A predicate with a KEYWORD operator - IS NULL, BETWEEN, IN, LIKE - has
no '=', so the WHOLE predicate became the "column", failed the test,
and a valid cursor was refused. DeclareOperandParser handles both forms
and strips a T.COL qualifier.

CORRECTION 3 - QUERYNO was 0-BASED.

_queryno() received enumerate()'s index, so the first cursor rendered
QUERYNO 253 while CursorDeclareBuilder rendered 254 for the same
cursor. DB2 EXPLAIN identifies a statement by QUERYNO; two generators
with two schemes cannot both be tied back to the documented access
path. Cursor order is 1-based here too.

CORRECTION 4 - a resolver failure aborted the whole block.

columns_for_table() was called bare. A thin or broken DCLGEN raised out
of generate() and no declaration at all was produced.
DeclareColumnOwnership reports and stands down.

CORRECTION 5 - the injected diagnostics list was discarded.

    def __init__(self, ..., diagnostics: list[str] | None = None):
        self.messages = diagnostics if diagnostics is not None else []
    def generate(self, specs):
        self.messages = []          <- rebinds, caller's list never filled

The caller's list stayed empty for every run. Messages are appended to
the injected list now and reset() is explicit.

CORRECTION 6 - the docstring asserted a WITHDRAWN premise.

"A cursor with NO WHERE clause is a parent/root cursor and never
carries ORDER BY" came from ONE sample. Manual reference VMDZ7200 ends
its ROOT cursor with ORDER BY NR_ID_479BFAS ASC, and
ENFORCE_ORDER_BY_RETENTION is True. This file read
PARENT_CURSOR_KEEPS_ORDER_BY directly and never consulted the master
switch. DeclareOrderByPlanner owns that decision for both generators.

CORRECTION 7 - ORDER BY entries were neither owned nor de-duplicated.

The FILLER placeholder that binds as SQLCODE -206, and the
'NR_ID ASC' / 'NR_ID DESC' pair DB2 rejects outright, both reached the
legacy output unchecked.

Clean Architecture:
- Every literal lives in rules/.
- No regex is defined in this package.
- No program, record, table, cursor or host variable name is hardcoded.
"""

from __future__ import annotations

from converter.generators.cursor_declaration.legacy_banner_builder import (
    LegacyBannerBuilder,
)
from converter.generators.cursor_declaration.legacy_clause_renderer import (
    LegacyClauseRenderer,
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
from rules.cursor_declaration_legacy import FIRST_CURSOR_ORDER
from rules.cursor_declaration_rules import (
    ENFORCE_ORDER_BY_COLUMN_OWNERSHIP,
    ENFORCE_WHERE_COLUMN_OWNERSHIP,
)

BLOCK_SEPARATOR = ""


class CursorDeclarationGenerator:
    """Builds the WORKING-STORAGE cursor declaration block."""

    def __init__(
        self,
        column_name_resolver,
        diagnostics: list[str] | None = None,
    ) -> None:
        self.column_name_resolver = column_name_resolver

        self.diagnostics = DeclareDiagnostics()
        # Honour an injected collector. See CORRECTION 5.
        if diagnostics is not None:
            self.diagnostics.messages = diagnostics

        self.ownership = DeclareColumnOwnership(
            diagnostics=self.diagnostics,
            column_name_resolver=column_name_resolver,
        )
        self.order_by = DeclareOrderByPlanner(self.diagnostics)
        self.refusal = DeclareRefusal(self.diagnostics)
        self.banner = LegacyBannerBuilder()
        self.renderer = LegacyClauseRenderer()

    @property
    def messages(self) -> list[str]:
        return self.diagnostics.messages

    def reset(self) -> None:
        """Drop state from the previous program."""
        self.diagnostics.reset()
        self.ownership.reset()

    # =================================================================
    # Public entry point
    # =================================================================
    def generate(self, specs: list[dict[str, object]]) -> list[str]:
        """Render every cursor declaration, in cursor order.

        Returns a flat list of COBOL body lines (no sequence numbers).
        The fixed-format writer applies columns 1-6, 7 and 73-80.
        """
        if not specs:
            return []

        lines: list[str] = []
        total = len(specs)

        for index, raw in enumerate(specs):
            block = self._declaration(
                spec=CursorSpec.read(raw),
                cursor_order=index + FIRST_CURSOR_ORDER,
                is_last=index == total - 1,
            )
            if not block:
                continue
            if lines:
                lines.append(BLOCK_SEPARATOR)
            lines.extend(block)

        return lines

    # =================================================================
    # One declaration
    # =================================================================
    def _declaration(
        self,
        spec: CursorSpec,
        cursor_order: int,
        is_last: bool,
    ) -> list[str]:
        if not spec.cursor_name:
            return self.refusal.no_cursor_name()

        if not spec.table_name:
            return self.refusal.no_table(spec.cursor_name)

        columns = self._unique(spec.select_columns)
        if not columns:
            return self.refusal.no_columns(spec.cursor_name, spec.table_name)

        conditions = self._unique(spec.where_conditions)

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

        order_by = self.order_by.plan(spec, bool(conditions), owned)

        lines = self.banner.banner(spec.table_name)
        lines.extend(
            self.renderer.render(
                cursor=spec.cursor_name,
                table=spec.table_name,
                columns=columns,
                conditions=conditions,
                order_by=order_by,
                cursor_order=cursor_order,
                is_last=is_last,
            )
        )

        self.diagnostics.log(
            "declared_cursor",
            cursor=spec.cursor_name,
            table=spec.table_name,
            count=len(columns),
            queryno=self.renderer.queryno(cursor_order),
        )
        return lines

    # =================================================================
    # Helpers
    # =================================================================
    @staticmethod
    def _unique(values) -> list[str]:
        """Order preserved, blanks and repeats dropped.

        SELECT order is AUTHORITATIVE: the FETCH INTO host list is built
        from the same sequence, so a mismatch here silently corrupts
        data.
        """
        out: list[str] = []
        seen: set[str] = set()

        for value in list(values or []):
            text = str(value or "").strip()
            if not text or text in seen:
                continue
            seen.add(text)
            out.append(text)

        return out


__all__ = ["CursorDeclarationGenerator"]
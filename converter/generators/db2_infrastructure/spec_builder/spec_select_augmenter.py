# LOCATION: converter/generators/db2_infrastructure/spec_builder/spec_select_augmenter.py
# ACTION: CREATE NEW FILE
"""Adds the columns a cursor must project but usage analysis missed.

A minimal usage-driven SELECT can still omit two kinds of column that
the cursor is nonetheless required to expose:

  1. ORDER BY columns of the same cursor.
  2. Parent join columns referenced by a CHILD cursor's WHERE. The child
     filters on the parent host variables, so the parent FETCH must
     populate them, which means the parent SELECT must list them.

Without (2) the parent host variables stay empty and the child
predicate is evaluated against blanks - a correctness bug, not a
cosmetic one.

FETCH host variables are re-resolved for every spec whose SELECT grew,
because SELECT and INTO are kept synchronized BY POSITION.
"""

from __future__ import annotations

from converter.generators.db2_infrastructure.spec_builder.spec_where_builder import (
    SpecWhereBuilder,
)
from converter.services.name_normalizer import NameNormalizer
from rules.cursor_spec import (
    SPEC_HOST_VARIABLES,
    SPEC_ORDER_BY_COLUMNS,
    SPEC_SELECT_COLUMNS,
    SPEC_TABLE_NAME,
    SPEC_WHERE_CONDITIONS,
)


class SpecSelectAugmenter:
    """Grows SELECT lists, then re-syncs the INTO lists."""

    def __init__(self, host_variable_resolver, where_builder: SpecWhereBuilder) -> None:
        self.host_variable_resolver = host_variable_resolver
        self.where_builder = where_builder

    def augment(self, specs: list[dict[str, object]]) -> None:
        by_table = {
            NameNormalizer.normalize(str(spec.get(SPEC_TABLE_NAME, ""))): spec
            for spec in specs
            if str(spec.get(SPEC_TABLE_NAME, "")).strip()
        }

        for spec in specs:
            self._add_own_order_by(spec)
            self._add_parent_join_columns(spec, by_table)

        self._resync_host_variables(specs)

    # ---- (1) this cursor's own ORDER BY
    def _add_own_order_by(self, spec: dict[str, object]) -> None:
        for expression in spec.get(SPEC_ORDER_BY_COLUMNS, []) or []:
            words = str(expression).strip().split()
            if words:
                self.add_column(spec, words[0])

    # ---- (2) the parent columns this child filters on
    def _add_parent_join_columns(
        self,
        spec: dict[str, object],
        by_table: dict[str, dict[str, object]],
    ) -> None:
        for condition in spec.get(SPEC_WHERE_CONDITIONS, []) or []:
            table, column = self.where_builder.parent_reference(str(condition))
            if not table or not column:
                continue

            parent_spec = by_table.get(table)
            if parent_spec is not None:
                self.add_column(parent_spec, column)

    # ---- INTO must follow SELECT, position for position
    def _resync_host_variables(self, specs: list[dict[str, object]]) -> None:
        for spec in specs:
            spec[SPEC_HOST_VARIABLES] = (
                self.host_variable_resolver.host_references_for_columns(
                    table_name=str(spec.get(SPEC_TABLE_NAME, "")),
                    columns=list(spec.get(SPEC_SELECT_COLUMNS, []) or []),
                )
            )

    @staticmethod
    def add_column(spec: dict[str, object], column: str) -> None:
        normalized = NameNormalizer.normalize(column)
        if not normalized:
            return

        columns = list(spec.get(SPEC_SELECT_COLUMNS, []) or [])
        existing = {NameNormalizer.normalize(item) for item in columns}
        if normalized in existing:
            return

        columns.append(normalized)
        spec[SPEC_SELECT_COLUMNS] = columns


__all__ = ["SpecSelectAugmenter"]
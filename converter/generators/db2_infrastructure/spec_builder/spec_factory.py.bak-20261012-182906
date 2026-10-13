"""Creates raw cursor specification dictionaries from IDMS operations."""

from __future__ import annotations

from converter.generators.db2_infrastructure.spec_builder.spec_build_context import (
    SpecBuildContext,
)
from converter.services.name_normalizer import NameNormalizer
from rules.cursor_spec import (
    CURSOR_OPERATIONS,
    SPEC_CLOSE_PARAGRAPH,
    SPEC_CURSOR_NAME,
    SPEC_CURSOR_ORDER,
    SPEC_FETCH_PARAGRAPH,
    SPEC_HOST_VARIABLES,
    SPEC_IS_PARENT_CURSOR,
    SPEC_OPEN_PARAGRAPH,
    SPEC_ORDER_BY_COLUMNS,
    SPEC_RECORD_NAME,
    SPEC_SELECT_COLUMNS,
    SPEC_SET_NAME,
    SPEC_TABLE_NAME,
    SPEC_WHERE_CONDITIONS,
)


class SpecFactory:
    """Creates raw specifications before cross-spec augmentation."""

    def __init__(
        self,
        owner,
        relationship_policy,
        parent_classifier,
    ) -> None:
        self.owner = owner
        self.relationship_policy = relationship_policy
        self.parent_classifier = parent_classifier

    def build(
        self,
        context: SpecBuildContext,
    ) -> list[dict[str, object]]:
        specs: list[dict[str, object]] = []
        seen: set[tuple[str, str, str]] = set()
        cursor_order = 1

        for operation in context.operations:
            spec = self._create_spec(
                operation=operation,
                cursor_order=cursor_order,
                seen=seen,
                context=context,
            )
            if spec is None:
                continue

            specs.append(spec)
            cursor_order += 1

        return specs

    def _create_spec(
        self,
        operation,
        cursor_order: int,
        seen: set[tuple[str, str, str]],
        context: SpecBuildContext,
    ) -> dict[str, object] | None:
        operation_name = str(
            getattr(operation, "operation", "") or ""
        ).upper()
        if operation_name not in CURSOR_OPERATIONS:
            return None

        record = NameNormalizer.normalize(
            getattr(operation, "record_name", "")
        )
        if not record:
            return None

        set_name = NameNormalizer.normalize(
            getattr(operation, "set_name", "")
        )
        table = self.owner.table_name_resolver.table_for_record(record)
        if not table:
            return None

        duplicate_key = (set_name, record, table)
        if duplicate_key in seen:
            return None
        seen.add(duplicate_key)

        paragraphs = self.owner._cursor_paragraph_spec(
            cursor_order=cursor_order,
            table_name=table,
        )

        select_columns = (
            self.owner.cursor_column_resolver.select_columns_for_record(
                record_name=record,
                field_usage_analysis=context.field_usage_analysis,
                force_full_record=record in context.materialised_records,
            )
        )

        where_conditions = self.relationship_policy.where_conditions(
            record=record,
            navigated_records=context.navigated_records,
            lrf_cursors=context.lrf_cursors,
        )

        return {
            SPEC_SET_NAME: set_name,
            SPEC_RECORD_NAME: record,
            SPEC_TABLE_NAME: table,
            SPEC_CURSOR_NAME: (
                self.owner.cursor_name_resolver.cursor_name_from_table(table)
            ),
            SPEC_SELECT_COLUMNS: select_columns,
            SPEC_HOST_VARIABLES: (
                self.owner.host_variable_resolver.host_references_for_columns(
                    table_name=table,
                    columns=select_columns,
                )
            ),
            SPEC_WHERE_CONDITIONS: where_conditions,
            SPEC_ORDER_BY_COLUMNS: (
                self.owner.cursor_column_resolver.order_by_columns_for_record(
                    record
                )
            ),
            SPEC_OPEN_PARAGRAPH: paragraphs["open_paragraph"],
            SPEC_FETCH_PARAGRAPH: paragraphs["fetch_paragraph"],
            SPEC_CLOSE_PARAGRAPH: paragraphs["close_paragraph"],
            SPEC_CURSOR_ORDER: cursor_order,
            SPEC_IS_PARENT_CURSOR: self.parent_classifier.is_parent(
                where_conditions=where_conditions,
                fetch_paragraph=paragraphs["fetch_paragraph"],
            ),
        }


__all__ = ["SpecFactory"]
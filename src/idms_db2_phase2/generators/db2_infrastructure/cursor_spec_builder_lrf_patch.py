"""Enhanced cursor spec builder with LRF support.

This module replaces the WHERE clause detection logic in cursor_spec_builder.py
to properly handle LRF-expanded cursors which need WHERE conditions even when
the parent record hasn't been explicitly navigated in an OBTAIN operation.
"""

from idms_db2_phase2.services.name_normalizer import NameNormalizer


def build_with_lrf_support(
    self,
    operations: list,
    cobol_text: str = "",
    field_usage_analysis=None,
    lrf_cursor_where_resolver=None,
) -> list[dict]:
    """Enhanced build() that detects LRF cursors and generates WHERE clauses.

    This function replaces the core logic in CursorSpecBuilder.build() to:
    1. Extract LRF expansion markers from COBOL comments
    2. Generate WHERE conditions for LRF-expanded cursors
    3. Ensure key columns used in WHERE are selected
    4. Correct ORDER BY direction for LRF NEXT operations

    Args:
        self: CursorSpecBuilder instance
        operations: List of IDMS operations from parser
        cobol_text: Full COBOL source text (contains LRF markers)
        field_usage_analysis: Field usage analysis result
        lrf_cursor_where_resolver: Instance of LrfCursorWhereResolver

    Returns:
        List of cursor spec dicts with proper WHERE/SELECT/ORDER BY
    """
    from idms_db2_phase2.analyzers.field_usage_analyzer import (
        FieldUsageAnalyzer,
    )

    output: list[dict[str, object]] = []
    seen: set[tuple[str, str, str]] = set()
    cursor_order = 1

    if field_usage_analysis is None:
        field_usage_analysis = FieldUsageAnalyzer(
            mapping_repository=self.owner.mapping_repository,
            table_name_resolver=self.owner.table_name_resolver,
        ).analyze(cobol_text)

    # Records explicitly positioned by OBTAIN/FIND in the program
    navigated_records = self._navigated_records(operations)

    # Extract LRF expansion markers from COBOL source
    lrf_cursors = {}
    if lrf_cursor_where_resolver:
        lrf_cursors = lrf_cursor_where_resolver.extract_lrf_cursors_from_cobol(
            cobol_text
        )

    for operation in operations or []:
        operation_name = str(operation.operation or "").upper()
        if operation_name not in {"OBTAIN_FIRST", "OBTAIN_NEXT", "FIND_FIRST"}:
            continue

        record_name = NameNormalizer.normalize(operation.record_name)
        set_name = NameNormalizer.normalize(operation.set_name)
        if not record_name:
            continue

        table_name = self.owner.table_name_resolver.table_for_record(
            record_name
        )
        if not table_name:
            continue

        key = (set_name, record_name, table_name)
        if key in seen:
            continue
        seen.add(key)

        cursor_name = (
            self.owner.cursor_name_resolver.cursor_name_from_table(
                table_name
            )
        )
        paragraph_spec = self.owner._cursor_paragraph_spec(
            cursor_order=cursor_order,
            table_name=table_name,
        )
        select_columns = (
            self.owner.cursor_column_resolver.select_columns_for_record(
                record_name=record_name,
                field_usage_analysis=field_usage_analysis,
            )
        )
        relationship = (
            self.owner.relationship_resolver.resolve_for_child_record(
                record_name
            )
        )
        parent_record = NameNormalizer.normalize(
            relationship.parent_record if relationship else ""
        )

        # ============================================================
        # NEW LOGIC: Check if this is an LRF-expanded cursor
        # ============================================================
        lrf_cursor_info = lrf_cursors.get(record_name, {})
        is_lrf_expanded = lrf_cursor_info.get("is_lrf_expanded", False)

        # WHERE clause logic:
        # - Old: Only if parent is in navigated_records
        # - New: Also if LRF-expanded (even if parent not explicitly navigated)
        if parent_record and parent_record in navigated_records:
            # Explicit parent navigation
            where_conditions = self._where_conditions_from_relationship(
                relationship.conditions
            )
        elif is_lrf_expanded and lrf_cursor_where_resolver:
            # LRF-expanded cursor: generate WHERE from relationship
            where_conditions = (
                lrf_cursor_where_resolver.where_conditions_for_lrf_cursor(
                    record_name, lrf_cursor_info
                )
            )
        else:
            where_conditions = []

        # ============================================================
        # NEW LOGIC: Fix ORDER BY direction for LRF NEXT
        # ============================================================
        order_by_columns = (
            self.owner.cursor_column_resolver.order_by_columns_for_record(
                record_name
            )
        )
        if is_lrf_expanded and lrf_cursor_where_resolver:
            order_by_columns = (
                lrf_cursor_where_resolver.resolve_order_by_direction_for_lrf(
                    record_name, lrf_cursor_info, order_by_columns
                )
            )

        host_variables = (
            self.owner.host_variable_resolver.host_references_for_columns(
                table_name=table_name,
                columns=select_columns,
            )
        )

        spec = {
            "set_name": set_name,
            "record_name": record_name,
            "table_name": table_name,
            "cursor_name": cursor_name,
            "select_columns": select_columns,
            "host_variables": host_variables,
            "where_conditions": where_conditions,
            "order_by_columns": order_by_columns,
            "open_paragraph": paragraph_spec["open_paragraph"],
            "fetch_paragraph": paragraph_spec["fetch_paragraph"],
            "close_paragraph": paragraph_spec["close_paragraph"],
            "cursor_order": cursor_order,
            "is_lrf_expanded": is_lrf_expanded,  # Track LRF status
        }

        output.append(spec)
        cursor_order += 1

    # Augment SELECT columns to include ORDER BY and WHERE-referenced keys
    self._augment_select_columns(output)

    # Additional augmentation for LRF cursor key columns
    if lrf_cursor_where_resolver:
        for spec in output:
            record_name = NameNormalizer.normalize(
                str(spec.get("record_name", ""))
            )
            lrf_info = lrf_cursors.get(record_name, {})
            if lrf_info.get("is_lrf_expanded"):
                lrf_cursor_where_resolver.augment_select_for_lrf_keys(
                    spec, lrf_info
                )

    return output


# Integration point: Monkey-patch or replace the build method
def integrate_lrf_support_into_cursor_spec_builder(lrf_resolver):
    """Integrate LRF support into CursorSpecBuilder.

    Call this during initialization to enable LRF WHERE clause generation.

    Args:
        lrf_resolver: Instance of LrfCursorWhereResolver configured with
                     the necessary dependencies (relationship_resolver, etc.)
    """
    from idms_db2_phase2.generators.db2_infrastructure.cursor_spec_builder import (
        CursorSpecBuilder,
    )

    # Store the original build method
    original_build = CursorSpecBuilder.build

    # Create wrapper that calls the enhanced logic
    def wrapped_build(
        self,
        operations: list,
        cobol_text: str = "",
        field_usage_analysis=None,
    ):
        """Wrapper that adds LRF support."""
        return build_with_lrf_support(
            self,
            operations=operations,
            cobol_text=cobol_text,
            field_usage_analysis=field_usage_analysis,
            lrf_cursor_where_resolver=lrf_resolver,
        )

    # Replace the method
    CursorSpecBuilder.build = wrapped_build
    return original_build

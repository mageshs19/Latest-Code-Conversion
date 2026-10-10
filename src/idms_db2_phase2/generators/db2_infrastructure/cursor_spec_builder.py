# LOCATION: src/idms_db2_phase2/generators/db2_infrastructure/cursor_spec_builder.py
# ACTION: CREATE NEW FILE

"""Builds cursor specifications from IDMS operations."""

from __future__ import annotations

import re

from idms_db2_phase2.analyzers.field_usage_analyzer import FieldUsageAnalyzer
from idms_db2_phase2.domain.models import IdmsOperation
from idms_db2_phase2.services.name_normalizer import NameNormalizer
from patterns.record_materialisation_patterns import WHOLE_RECORD_MOVE_PATTERN

CURSOR_OPERATIONS = {
    "OBTAIN_FIRST",
    "OBTAIN_NEXT",
    "FIND_FIRST",
}


class CursorSpecBuilder:
    def __init__(self, owner) -> None:
        # owner exposes resolvers, mapping_repository, cursor_column_resolver,
        # relationship_resolver, cursor_name_resolver, table_name_resolver,
        # host_variable_resolver, _cursor_paragraph_spec.
        self.owner = owner

    def build(
        self,
        operations: list[IdmsOperation],
        cobol_text: str = "",
        field_usage_analysis=None,
    ) -> list[dict[str, object]]:
        output: list[dict[str, object]] = []
        seen: set[tuple[str, str, str]] = set()
        cursor_order = 1

        if field_usage_analysis is None:
            field_usage_analysis = FieldUsageAnalyzer(
                mapping_repository=self.owner.mapping_repository,
                table_name_resolver=self.owner.table_name_resolver,
            ).analyze(cobol_text)

        # Records this program actually positions. A parent WHERE join is
        # only valid when the parent is obtained here; otherwise its host
        # variables are never populated and the predicate is spurious.
        navigated_records = self._navigated_records(operations)

        # Records copied out as a whole ('MOVE <record> TO <target>'). The
        # materialisation composer later emits one MOVE per mapped column
        # for these, so the cursor MUST fetch the full record or those
        # columns are moved as zeros.
        materialised_records = self._materialised_records(cobol_text)

        # LRF (Large Result Set) cursor detection via comment markers
        # Pattern: *DB2: Expanded LRF FIRST/NEXT <subsceme> WHERE <sweep> -> <record>
        lrf_cursors = self._extract_lrf_cursors_from_comments(cobol_text)

        for operation in operations or []:
            operation_name = str(operation.operation or "").upper()
            if operation_name not in CURSOR_OPERATIONS:
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
                    force_full_record=record_name in materialised_records,
                )
            )
            relationship = (
                self.owner.relationship_resolver.resolve_for_child_record(
                    record_name
                )
            )
            parent_record = NameNormalizer.normalize(
                relationship.parent_record
            )
            if parent_record and parent_record in navigated_records:
                where_conditions = self._where_conditions_from_relationship(
                    relationship.conditions
                )
            else:
                where_conditions = []
            
            # LRF WHERE clause: Check if this record appears in LRF cursors
            # from expanded comments like *DB2: Expanded LRF FIRST ...
            if record_name in lrf_cursors:
                lrf_info = lrf_cursors[record_name]
                # Use relationship resolver to generate WHERE from parent keys
                if relationship and relationship.conditions:
                    lrf_where = self._where_conditions_from_relationship(
                        relationship.conditions
                    )
                    where_conditions.extend(lrf_where)
            order_by_columns = (
                self.owner.cursor_column_resolver.order_by_columns_for_record(
                    record_name
                )
            )
            host_variables = (
                self.owner.host_variable_resolver.host_references_for_columns(
                    table_name=table_name,
                    columns=select_columns,
                )
            )

            output.append(
                {
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
                    "is_parent_cursor": self._is_parent_cursor(paragraph_spec["fetch_paragraph"]),
                }
            )
            cursor_order += 1

        self._augment_select_columns(output)

        return output

    def _augment_select_columns(
        self,
        specs: list[dict[str, object]],
    ) -> None:
        """Ensure each cursor SELECT also carries the columns it must expose.

        A minimal usage-driven SELECT can still omit two kinds of columns
        that the cursor is nonetheless required to project:

        1. ORDER BY columns of the same cursor.
        2. Parent join columns referenced by a child cursor's WHERE. The
           child filters on the parent host variables, so the parent FETCH
           must populate them, which means the parent SELECT must list them.

        Without (2) the parent host variables stay empty and the child
        predicate is evaluated against blanks - a correctness bug, not a
        cosmetic one.
        """
        specs_by_table: dict[str, dict[str, object]] = {}
        for spec in specs:
            table = NameNormalizer.normalize(str(spec.get("table_name", "")))
            if table:
                specs_by_table[table] = spec

        for spec in specs:
            # (1) self ORDER BY columns.
            for expression in spec.get("order_by_columns", []) or []:
                column = str(expression).strip().split()[0] if str(
                    expression
                ).strip() else ""
                self._add_select_column(spec, column)

            # (2) parent join columns referenced by this child's WHERE.
            for condition in spec.get("where_conditions", []) or []:
                parent_table, parent_column = self._parent_ref_from_condition(
                    str(condition)
                )
                if not parent_table or not parent_column:
                    continue
                parent_spec = specs_by_table.get(parent_table)
                if parent_spec is not None:
                    self._add_select_column(parent_spec, parent_column)

        # Re-resolve FETCH host variables for any spec whose SELECT grew.
        for spec in specs:
            table_name = str(spec.get("table_name", ""))
            columns = list(spec.get("select_columns", []) or [])
            spec["host_variables"] = (
                self.owner.host_variable_resolver.host_references_for_columns(
                    table_name=table_name,
                    columns=columns,
                )
            )

    @staticmethod
    def _add_select_column(spec: dict[str, object], column: str) -> None:
        normalized = NameNormalizer.normalize(column)
        if not normalized:
            return
        columns = list(spec.get("select_columns", []) or [])
        existing = {NameNormalizer.normalize(c) for c in columns}
        if normalized not in existing:
            columns.append(normalized)
            spec["select_columns"] = columns

    @staticmethod
    def _parent_ref_from_condition(condition: str) -> tuple[str, str]:
        """'CHILD_COL = :DCLDZBEFFTV.CT-RKTPROD-479BEFF' -> (table, column).

        Returns the parent table ('DZBEFFTV') and the parent column
        ('CT_RKTPROD_479BEFF') the host reference resolves to.
        """
        text = str(condition or "")
        if ":" not in text or "." not in text:
            return "", ""
        host = text.split(":", 1)[1].strip()
        if "." not in host:
            return "", ""
        dcl_name, host_field = host.split(".", 1)
        dcl_name = dcl_name.strip().upper()
        host_field = host_field.strip()
        # Host group name is 'DCL' + table name.
        table = dcl_name[3:] if dcl_name.startswith("DCL") else dcl_name
        column = NameNormalizer.normalize(host_field.replace("-", "_"))
        return NameNormalizer.normalize(table), column


    def _navigated_records(
        self,
        operations: list[IdmsOperation],
    ) -> set[str]:
        """Records positioned by an OBTAIN/FIND anywhere in the program."""
        records: set[str] = set()
        for operation in operations or []:
            name = str(getattr(operation, "operation", "") or "").upper()
            if not (name.startswith("OBTAIN") or name.startswith("FIND")):
                continue
            record = NameNormalizer.normalize(
                getattr(operation, "record_name", "")
            )
            if record:
                records.add(record)
        return records

    @staticmethod
    def _materialised_records(cobol_text: str) -> set[str]:
        """Records copied whole via 'MOVE <record> TO <target>'.

        The record materialisation composer keys off this exact statement
        and later emits one MOVE per mapped column. The cursor for such a
        record must project the full record, so the materialised MOVEs
        read fetched data rather than a zero-filled host group.
        """
        records: set[str] = set()
        for raw in str(cobol_text or "").split("\n"):
            # Strip the fixed-format sequence area / indicator column so the
            # pattern (anchored at ^MOVE) matches the statement body, then
            # drop the columns 73-80 sequence tail.
            body = raw[7:] if len(raw) > 7 else raw
            if len(body) > 65:
                body = body[:65]
            match = WHOLE_RECORD_MOVE_PATTERN.match(body.strip())
            if not match:
                continue
            record = NameNormalizer.normalize(match.group("record"))
            if record:
                records.add(record)
        return records

    @staticmethod
    def _extract_lrf_cursors_from_comments(cobol_text: str) -> dict[str, dict]:
        """Extract LRF cursor info from *DB2: Expanded LRF comments.

        COBOL LRF expansion adds comments that may span multiple lines:
        
        Line 1: 002210*DB2: Expanded LRF NEXT VMBTL07-R01 WHERE ALL-VMBEVEF-BY-VMBEFF ->
        Line 2: 002220*  VMBEVEF WITHIN VMBEFF-VMBEVEF.
        
        Or on a single line:
        002460*DB2: Expanded LRF FIRST VMBTL03-R01 WHERE SWEEP-VMBFAS -> VMBFAS
        
        COBOL fixed-format structure:
        - Columns 0-5: sequence
        - Column 6: indicator (*)
        - Columns 7-72: body (stripped before regex)
        - Columns 73-80: sequence tail
        
        Returns dict of record_name → {mode, sweep_condition, subsceme}.
        """
        lrf_cursors: dict[str, dict] = {}
        lines = str(cobol_text or "").split("\n")
        
        # Pattern matches stripped body: "DB2: Expanded LRF FIRST ... WHERE ... -> ..."
        # (no leading * because indicator column is stripped)
        lrf_single_pattern = re.compile(
            r"DB2:\s+Expanded LRF\s+(FIRST|NEXT)\s+(\S+)\s+WHERE\s+(\S+)\s+->\s+(\S+)",
            re.IGNORECASE
        )
        # For multi-line: ending with "-> " and possibly trailing junk
        lrf_multi_start_pattern = re.compile(
            r"DB2:\s+Expanded LRF\s+(FIRST|NEXT)\s+(\S+)\s+WHERE\s+(\S+)\s*->\s*$",
            re.IGNORECASE
        )
        
        for i, line in enumerate(lines):
            # Strip COBOL fixed-format sequence area and tail
            # Columns 0-6: sequence + indicator, Columns 7-72: body, 73-80: sequence tail
            body = line[7:] if len(line) > 7 else line
            if len(body) > 65:
                body = body[:65]  # Keep only columns 7-72 (drop 73-80)
            
            # Try single-line match first
            match = lrf_single_pattern.search(body)
            if match:
                mode, subsceme, sweep, record = match.groups()
                normalized_record = NameNormalizer.normalize(record)
                if normalized_record not in lrf_cursors:
                    lrf_cursors[normalized_record] = {
                        "mode": mode.upper(),
                        "subsceme": subsceme.upper(),
                        "sweep_condition": sweep.upper(),
                        "is_lrf_expanded": True
                    }
                continue
            
            # Try multi-line match
            match = lrf_multi_start_pattern.search(body)
            if not match or i + 1 >= len(lines):
                continue
            
            mode, subsceme, sweep = match.groups()
            # Next line should have the record name (continuation line with *)
            next_line = lines[i + 1]
            # Extract record name from continuation (format: "*  <record> ...")
            record_match = re.search(r"\*?\s+(\w+)", next_line)
            if not record_match:
                continue
            record = record_match.group(1)
            normalized_record = NameNormalizer.normalize(record)
            if normalized_record not in lrf_cursors:
                lrf_cursors[normalized_record] = {
                    "mode": mode.upper(),
                    "subsceme": subsceme.upper(),
                    "sweep_condition": sweep.upper(),
                    "is_lrf_expanded": True
                }
        
        return lrf_cursors

    def include_names(
        self,
        cursor_specs: list[dict[str, object]],
    ) -> list[str]:
        output: list[str] = []
        seen: set[str] = set()

        for spec in cursor_specs or []:
            table_name = NameNormalizer.normalize(
                str(spec.get("table_name", ""))
            )
            if not table_name:
                continue
            include_name = self.owner.line_utils.normalize_include_name(
                table_name
            )
            if not include_name or include_name in seen:
                continue
            seen.add(include_name)
            output.append(include_name)

        return output

    def spec_messages(
        self,
        cursor_specs: list[dict[str, object]],
    ) -> list[str]:
        messages: list[str] = []

        for spec in cursor_specs:
            cursor_name = str(spec.get("cursor_name", ""))
            record_name = str(spec.get("record_name", ""))
            table_name = str(spec.get("table_name", ""))
            select_columns = list(spec.get("select_columns", []))
            host_variables = list(spec.get("host_variables", []))

            if not table_name:
                messages.append(
                    f"DB2 infrastructure: cursor {cursor_name} has no "
                    f"resolved DB2 table for record {record_name}."
                )
            if not select_columns:
                messages.append(
                    f"DB2 infrastructure: cursor {cursor_name} has no "
                    f"resolved SELECT columns for record {record_name}."
                )
            if not host_variables:
                messages.append(
                    f"DB2 infrastructure: cursor {cursor_name} has no "
                    f"resolved FETCH host variables for record {record_name}."
                )

        return messages

    def _where_conditions_from_relationship(self, conditions) -> list[str]:
        output: list[str] = []
        for condition in conditions or []:
            child_column = NameNormalizer.normalize(
                getattr(condition, "child_column", "")
            )
            parent_host = str(
                getattr(condition, "parent_host_reference", "") or ""
            ).strip()
            if not child_column or not parent_host:
                continue
            output.append(f"{child_column} = {parent_host}")
        return output

    def _is_parent_cursor(self, fetch_paragraph: str) -> bool:
        """
        Determine if this cursor is a parent cursor based on paragraph number.
        
        Parent cursors (OBTAIN FIRST) have fetch paragraphs in 700-series.
        Child cursors (OBTAIN NEXT) have fetch paragraphs in 800-series.
        
        Examples:
        - 710-OPEN, 720-FETCH, 730-CLOSE = parent (700-series)
        - 810-OPEN, 820-FETCH, 830-CLOSE = child (800-series)
        
        Args:
            fetch_paragraph: The fetch paragraph name (e.g., "720-FETCH-DZBFASC1")
        
        Returns:
            True if parent cursor (700-series), False if child (800-series)
        """
        if not fetch_paragraph:
            return False
        
        # Extract the paragraph number (first 3 digits)
        para_num = str(fetch_paragraph).split("-")[0] if "-" in str(fetch_paragraph) else ""
        
        if not para_num or len(para_num) < 3:
            return False
        
        # Get the first digit to determine series
        series_digit = para_num[0]
        
        # Parent cursors: 700-series (7xx)
        # Child cursors: 800-series (8xx)
        return series_digit == "7"


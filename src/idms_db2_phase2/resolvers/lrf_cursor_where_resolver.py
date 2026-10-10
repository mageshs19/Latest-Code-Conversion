"""Resolves WHERE clauses for LRF-expanded cursors.

When LRF expansion converts "OBTAIN WHERE <path>" to classical IDMS syntax,
it leaves a comment marker like:
    *DB2: Expanded LRF FIRST VMBTL03-R01 WHERE SWEEP-VMBFAS -> VMBFAS

This resolver extracts that information and generates the WHERE conditions
that should be applied to the resulting cursor, based on parent-child
key relationships.

Key insight: LRF OBTAIN FIRST and OBTAIN NEXT both need WHERE clauses
based on their access type (parent keys or relationship keys).
"""

from __future__ import annotations

import re
from idms_db2_phase2.services.name_normalizer import NameNormalizer


class LrfCursorWhereResolver:
    """Generates WHERE conditions for LRF-expanded cursors."""

    # Pattern: *DB2: Expanded LRF {mode} {lr} WHERE {keyword} -> {record} WITHIN {within}
    LRF_EXPANSION_PATTERN = re.compile(
        r"\*DB2:\s+Expanded LRF\s+"
        r"(FIRST|NEXT)\s+"  # mode: FIRST or NEXT
        r"(\w+)\s+"  # lr name
        r"WHERE\s+"
        r"(\w+)\s+"  # path keyword
        r"->\s+"
        r"(\w+)"  # record name
        r"(?:\s+WITHIN\s+(\w+))?",  # optional WITHIN clause
        re.IGNORECASE,
    )

    def __init__(
        self,
        *,
        relationship_resolver=None,
        cursor_column_resolver=None,
        host_variable_resolver=None,
        mapping_repository=None,
    ) -> None:
        self.relationship_resolver = relationship_resolver
        self.cursor_column_resolver = cursor_column_resolver
        self.host_variable_resolver = host_variable_resolver
        self.mapping_repository = mapping_repository

    def extract_lrf_cursors_from_cobol(
        self, cobol_text: str
    ) -> dict[str, dict[str, str]]:
        """Extract LRF expansion markers from COBOL source.

        Returns:
            {"record_name": {"mode": "FIRST", "path_keyword": "...", ...}, ...}
        """
        lrf_cursors: dict[str, dict[str, str]] = {}

        for line in (cobol_text or "").split("\n"):
            match = self.LRF_EXPANSION_PATTERN.search(line)
            if not match:
                continue

            mode, lr_name, path_keyword, record_name, within_set = match.groups()
            norm_record = NameNormalizer.normalize(record_name)

            if norm_record not in lrf_cursors:
                lrf_cursors[norm_record] = {
                    "mode": mode.upper(),
                    "lr_name": lr_name.upper(),
                    "path_keyword": path_keyword.upper(),
                    "within_set": (within_set or "").upper(),
                    "is_lrf_expanded": True,
                }

        return lrf_cursors

    def where_conditions_for_lrf_cursor(
        self,
        record_name: str,
        lrf_cursor_info: dict[str, str],
    ) -> list[str]:
        """Generate WHERE conditions for an LRF-expanded cursor.

        Args:
            record_name: Child record being fetched
            lrf_cursor_info: Dict with "mode", "path_keyword", etc.

        Returns:
            List of WHERE condition strings like:
            ["NR_CIO_479BFAS = :DCLDZBEFFTV.NR-CIO-FORM-AS", ...]
        """
        if not lrf_cursor_info.get("is_lrf_expanded"):
            return []

        # Get relationship info for this child record
        if self.relationship_resolver is None:
            return []

        relationship = self.relationship_resolver.resolve_for_child_record(
            record_name
        )

        if not relationship or not relationship.conditions:
            # No explicit relationship found; return empty
            return []

        # Convert relationship conditions to WHERE predicates
        where_conditions = []
        for condition in relationship.conditions:
            # condition has: child_column, parent_column, parent_host_reference
            child_col = str(condition.child_column or "")
            parent_host_ref = str(condition.parent_host_reference or "")

            if child_col and parent_host_ref:
                # Format: "CHILD_COL = :PARENT_DCL.PARENT_FIELD"
                predicate = f"{child_col} = {parent_host_ref}"
                where_conditions.append(predicate)

        return where_conditions

    def augment_select_for_lrf_keys(
        self,
        cursor_spec: dict[str, object],
        lrf_cursor_info: dict[str, str],
    ) -> None:
        """Ensure WHERE-referenced key columns are in the SELECT.

        When a cursor has WHERE conditions based on parent keys,
        those parent key columns must be selected from the parent table,
        or the host variables won't be populated.

        Args:
            cursor_spec: Dict with "select_columns", "where_conditions", etc.
            lrf_cursor_info: LRF metadata dict
        """
        if not lrf_cursor_info.get("is_lrf_expanded"):
            return

        where_conditions = cursor_spec.get("where_conditions", []) or []
        select_columns = list(cursor_spec.get("select_columns", []) or [])

        # Extract parent table and columns from WHERE predicates
        for condition in where_conditions:
            # Pattern: "PARENT_COL = :DCLPARENTTBL.PARENT_FIELD"
            if ":" not in condition or "." not in condition:
                continue

            host_part = condition.split(":", 1)[1].strip()
            dcl_name, host_field = host_part.split(".", 1)
            dcl_name = dcl_name.strip()

            # Derive parent column name from host field
            parent_col = NameNormalizer.normalize(
                host_field.strip().replace("-", "_")
            )

            # Add to SELECT if not already present
            existing = {NameNormalizer.normalize(c) for c in select_columns}
            if parent_col not in existing:
                select_columns.append(parent_col)

        cursor_spec["select_columns"] = select_columns

    def resolve_order_by_direction_for_lrf(
        self,
        record_name: str,
        lrf_cursor_info: dict[str, str],
        order_by_columns: list[str],
    ) -> list[str]:
        """Correct ORDER BY direction based on LRF access type.

        LRF OBTAIN NEXT typically requires DESC ordering on the key,
        while OBTAIN FIRST uses ASC.

        Args:
            record_name: Record being fetched
            lrf_cursor_info: LRF metadata with "mode" field
            order_by_columns: Current ORDER BY expressions

        Returns:
            Corrected ORDER BY expressions with proper ASC/DESC
        """
        if not lrf_cursor_info.get("is_lrf_expanded"):
            return order_by_columns

        if not order_by_columns:
            return order_by_columns

        mode = lrf_cursor_info.get("mode", "FIRST").upper()
        corrected = []

        for expr in order_by_columns or []:
            expr_str = str(expr).strip()

            # If mode is NEXT and no direction specified, default to DESC
            if mode == "NEXT" and "ASC" not in expr_str and "DESC" not in expr_str:
                corrected.append(f"{expr_str} DESC")
            elif mode == "FIRST" and "DESC" in expr_str and "ASC" not in expr_str:
                # If mode is FIRST but has DESC, change to ASC
                corrected.append(expr_str.replace("DESC", "ASC").strip())
            else:
                corrected.append(expr_str)

        return corrected

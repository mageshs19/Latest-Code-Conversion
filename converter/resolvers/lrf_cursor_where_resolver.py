# LOCATION: converter/resolvers/lrf_cursor_where_resolver.py
# ACTION: REPLACE ENTIRE FILE
"""Resolves WHERE clauses for LRF-expanded cursors.

LRF path expansion leaves a comment marker in the generated program:

    *DB2: Expanded LRF FIRST <logical-record> WHERE <keyword> -> <record>

This resolver reads that marker and generates the WHERE conditions that
belong on the resulting cursor, from parent-child key relationships.

CORRECTION - THE MARKER FORMAT HAD FOUR OWNERS

This module carried a PRIVATE copy of the marker regex. So did
converter/generators/lrf_host_variable_populator.py. The format is
owned and documented in patterns/cursor_spec/lrf_comment_patterns.py,
which publishes three forms: single-line, wrapped, and the continuation
record that opens a wrapped body.

The private copies drifted. The populator's copy anchored on the comment
indicator (\\*), which lives in column 7 - OUTSIDE the logical body - so
it could never match a stripped body and the pass was inert on every
program. This module's copy declared an optional WITHIN group and then
unpacked FIVE values from a FOUR-group match.

There is now ONE owner. The shared name is re-exported so existing
importers keep working; it is never re-assigned.

GROUP NAMES - READ BEFORE USING

The shared single-line pattern captures, in order:

    mode       FIRST | NEXT
    subschema  the LOGICAL RECORD name
    sweep      the PATH KEYWORD
    record     the TARGET RECORD

It does NOT capture a set or an area. A path keyword may resolve WITHIN
a SET (a join, which has a parent record) or WITHIN an AREA (an
unqualified sweep, which has no parent at all). Only the parsed
subschema knows which. Never infer it from the marker.
"""

from __future__ import annotations

from converter.services.name_normalizer import NameNormalizer
from patterns.cursor_spec.lrf_comment_patterns import (
    LRF_CONTINUATION_RECORD_PATTERN,
    LRF_EXPANSION_PATTERN as _SHARED_LRF_EXPANSION_PATTERN,
    LRF_EXPANSION_WRAPPED_PATTERN as _SHARED_LRF_WRAPPED_PATTERN,
)

_MARKER_PROBE = "EXPANDED LRF"


class LrfCursorWhereResolver:
    """Generates WHERE conditions for LRF-expanded cursors."""

    # One owner for the marker format. This module READS markers; it does
    # not define what a marker looks like.
    LRF_EXPANSION_PATTERN = _SHARED_LRF_EXPANSION_PATTERN
    LRF_EXPANSION_WRAPPED_PATTERN = _SHARED_LRF_WRAPPED_PATTERN
    LRF_CONTINUATION_RECORD_PATTERN = LRF_CONTINUATION_RECORD_PATTERN

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
        self.messages: list[str] = []

    # ------------------------------------------------------------------
    # Marker extraction
    # ------------------------------------------------------------------

    def extract_lrf_cursors_from_cobol(
        self,
        cobol_text: str,
    ) -> dict[str, dict[str, str]]:
        """Extract LRF expansion markers from COBOL source.

        Returns:
            {"<record>": {"mode": ..., "lr_name": ..., "path_keyword": ...,
                          "is_lrf_expanded": True}, ...}

        The set name is deliberately NOT returned. It is not in the
        marker; it belongs to the parsed subschema.
        """
        self.messages = []
        lrf_cursors: dict[str, dict[str, str]] = {}

        lines = str(cobol_text or "").splitlines()

        for index, line in enumerate(lines):
            body = self._logical_body(line)
            if not body.strip():
                continue

            match = self.LRF_EXPANSION_PATTERN.search(body)
            record_name = ""

            if match is not None:
                record_name = match.group("record")
            else:
                match = self.LRF_EXPANSION_WRAPPED_PATTERN.search(body)
                if match is None:
                    if _MARKER_PROBE in body.upper():
                        self.messages.append(
                            "LRF where resolver: line "
                            f"{index + 1} carries 'Expanded LRF' but does "
                            "not match the shared marker format."
                        )
                    continue
                record_name = self._continuation_record(lines, index)
                if not record_name:
                    continue

            norm_record = NameNormalizer.normalize(record_name)
            if norm_record in lrf_cursors:
                continue

            lrf_cursors[norm_record] = {
                "mode": str(match.group("mode")).upper(),
                "lr_name": str(match.group("subschema")).upper(),
                "path_keyword": str(match.group("sweep")).upper(),
                "record_name": str(record_name).upper(),
                "is_lrf_expanded": True,
            }

        return lrf_cursors

    # ------------------------------------------------------------------
    # WHERE generation
    # ------------------------------------------------------------------

    def where_conditions_for_lrf_cursor(
        self,
        record_name: str,
        lrf_cursor_info: dict[str, str],
    ) -> list[str]:
        """WHERE predicates for an LRF-expanded cursor.

        Returns an empty list when the path carries no relationship -
        an unqualified sweep has no join predicate and must not be given
        an invented one.
        """
        if not lrf_cursor_info.get("is_lrf_expanded"):
            return []

        if self.relationship_resolver is None:
            return []

        relationship = self.relationship_resolver.resolve_for_child_record(
            record_name
        )
        if not relationship or not getattr(relationship, "conditions", None):
            return []

        where_conditions: list[str] = []
        for condition in relationship.conditions:
            child_col = str(getattr(condition, "child_column", "") or "")
            parent_host_ref = str(
                getattr(condition, "parent_host_reference", "") or ""
            )
            if child_col and parent_host_ref:
                where_conditions.append(f"{child_col} = {parent_host_ref}")

        return where_conditions

    def augment_select_for_lrf_keys(
        self,
        cursor_spec: dict[str, object],
        lrf_cursor_info: dict[str, str],
    ) -> None:
        """Ensure WHERE-referenced key columns appear in the SELECT.

        A predicate host variable that is never selected is never
        populated, so the cursor silently filters on spaces or zeroes.
        """
        if not lrf_cursor_info.get("is_lrf_expanded"):
            return

        where_conditions = cursor_spec.get("where_conditions", []) or []
        select_columns = list(cursor_spec.get("select_columns", []) or [])
        existing = {NameNormalizer.normalize(c) for c in select_columns}

        for condition in where_conditions:
            text = str(condition)
            if ":" not in text or "." not in text:
                continue

            host_part = text.split(":", 1)[1].strip()
            if "." not in host_part:
                continue

            _dcl_name, host_field = host_part.split(".", 1)
            parent_col = NameNormalizer.normalize(
                host_field.strip().replace("-", "_")
            )
            if parent_col and parent_col not in existing:
                select_columns.append(parent_col)
                existing.add(parent_col)

        cursor_spec["select_columns"] = select_columns

    def resolve_order_by_direction_for_lrf(
        self,
        record_name: str,
        lrf_cursor_info: dict[str, str],
        order_by_columns: list[str],
    ) -> list[str]:
        """Correct ORDER BY direction from the LRF access mode."""
        if not lrf_cursor_info.get("is_lrf_expanded"):
            return order_by_columns
        if not order_by_columns:
            return order_by_columns

        mode = str(lrf_cursor_info.get("mode", "FIRST")).upper()
        corrected: list[str] = []

        for expr in order_by_columns:
            expr_str = str(expr).strip()
            upper = expr_str.upper()
            has_asc = " ASC" in f" {upper}"
            has_desc = " DESC" in f" {upper}"

            if mode == "NEXT" and not has_asc and not has_desc:
                corrected.append(f"{expr_str} DESC")
            elif mode == "FIRST" and has_desc and not has_asc:
                corrected.append(expr_str.replace("DESC", "ASC").strip())
            else:
                corrected.append(expr_str)

        return corrected

    # ------------------------------------------------------------------
    # Private: fixed-format access
    # ------------------------------------------------------------------

    @staticmethod
    def _logical_body(line: str) -> str:
        """Columns 8-72 of a fixed-format record, indicator removed."""
        text = str(line or "").rstrip("\r\n")
        if len(text) >= 72 and text[:6].strip().isdigit():
            return text[7:72]
        return text

    def _continuation_record(self, lines: list[str], index: int) -> str:
        """Record name opening the body after a wrapped marker."""
        for offset in range(index + 1, min(index + 3, len(lines))):
            body = self._logical_body(lines[offset]).strip()
            if not body:
                continue
            match = self.LRF_CONTINUATION_RECORD_PATTERN.match(body)
            if match:
                return match.group("record")
            break
        return ""


__all__ = ["LrfCursorWhereResolver"]
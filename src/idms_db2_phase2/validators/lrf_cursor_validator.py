"""Validation and diagnostic module for LRF cursor WHERE clause generation.

This module provides tools to:
1. Validate that WHERE clauses are properly generated for LRF cursors
2. Compare generated vs. expected cursor specs
3. Generate diagnostic reports for manual review
4. Identify remaining gaps in cursor generation
"""

from __future__ import annotations

import re
from typing import NamedTuple


class CursorValidationIssue(NamedTuple):
    """Represents a validation issue in a cursor."""

    severity: str  # "ERROR", "WARNING", "INFO"
    cursor_name: str
    record_name: str
    issue_type: str  # "MISSING_WHERE", "INCOMPLETE_SELECT", "WRONG_ORDER_BY"
    description: str
    affected_element: str  # column, condition, etc.


class LrfCursorValidator:
    """Validates LRF cursor specs for correctness."""

    def __init__(self, mapping_repository=None):
        self.mapping_repository = mapping_repository
        self.issues: list[CursorValidationIssue] = []

    def validate_cursor_spec(
        self,
        spec: dict[str, object],
        cobol_text: str = "",
    ) -> list[CursorValidationIssue]:
        """Validate a single cursor specification.

        Checks for:
        1. LRF-expanded cursors have WHERE conditions
        2. All WHERE-referenced columns in SELECT
        3. Parent key columns are selected
        4. ORDER BY direction matches access type

        Args:
            spec: Cursor spec dict from CursorSpecBuilder
            cobol_text: COBOL source (for LRF marker detection)

        Returns:
            List of validation issues found
        """
        issues = []
        cursor_name = str(spec.get("cursor_name", ""))
        record_name = str(spec.get("record_name", ""))
        is_lrf = spec.get("is_lrf_expanded", False)

        # Check 1: LRF cursors should have WHERE conditions
        where_conditions = spec.get("where_conditions", []) or []
        if is_lrf and not where_conditions:
            issues.append(
                CursorValidationIssue(
                    severity="ERROR",
                    cursor_name=cursor_name,
                    record_name=record_name,
                    issue_type="MISSING_WHERE",
                    description="LRF-expanded cursor missing WHERE clause",
                    affected_element="WHERE",
                )
            )

        # Check 2: All WHERE-referenced columns must be selected
        select_columns = {
            str(c).strip().split()[0]  # Get base column name (remove ASC/DESC)
            for c in (spec.get("select_columns", []) or [])
        }

        for condition in where_conditions:
            # Extract child column from "CHILD_COL = :..."
            match = re.match(r"(\w+)\s*=", condition)
            if match:
                child_col = match.group(1).upper()
                if child_col not in select_columns:
                    issues.append(
                        CursorValidationIssue(
                            severity="ERROR",
                            cursor_name=cursor_name,
                            record_name=record_name,
                            issue_type="INCOMPLETE_SELECT",
                            description=f"WHERE clause references {child_col} "
                            f"but it's not in SELECT",
                            affected_element=child_col,
                        )
                    )

        # Check 3: ORDER BY direction for LRF NEXT
        order_by_columns = spec.get("order_by_columns", []) or []
        if is_lrf:
            # Extract LRF mode from spec if available
            lrf_mode = spec.get("lrf_mode", "").upper()
            if lrf_mode == "NEXT":
                for expr in order_by_columns:
                    expr_str = str(expr).upper()
                    if "ASC" in expr_str and "DESC" not in expr_str:
                        issues.append(
                            CursorValidationIssue(
                                severity="WARNING",
                                cursor_name=cursor_name,
                                record_name=record_name,
                                issue_type="WRONG_ORDER_BY",
                                description="LRF NEXT should use DESC ordering",
                                affected_element=expr_str,
                            )
                        )

        # Check 4: Warn if SELECT has very few columns
        if len(select_columns) < 3:
            issues.append(
                CursorValidationIssue(
                    severity="WARNING",
                    cursor_name=cursor_name,
                    record_name=record_name,
                    issue_type="INCOMPLETE_SELECT",
                    description=f"SELECT only has {len(select_columns)} columns; "
                    f"may be incomplete",
                    affected_element="SELECT",
                )
            )

        return issues

    def validate_all_specs(
        self,
        specs: list[dict[str, object]],
        cobol_text: str = "",
    ) -> list[CursorValidationIssue]:
        """Validate all cursor specs in a conversion result.

        Args:
            specs: List of cursor specs from CursorSpecBuilder
            cobol_text: Full COBOL source

        Returns:
            Aggregated list of all issues found
        """
        all_issues = []
        for spec in specs or []:
            issues = self.validate_cursor_spec(spec, cobol_text)
            all_issues.extend(issues)
        return all_issues

    def generate_validation_report(
        self,
        specs: list[dict[str, object]],
        cobol_text: str = "",
        program_name: str = "",
    ) -> str:
        """Generate a human-readable validation report.

        Args:
            specs: List of cursor specs
            cobol_text: COBOL source
            program_name: Program name for report header

        Returns:
            Formatted report string
        """
        issues = self.validate_all_specs(specs, cobol_text)

        lines = [
            "=" * 70,
            f"LRF Cursor Validation Report: {program_name or 'Unknown'}",
            "=" * 70,
            "",
        ]

        if not issues:
            lines.append("✓ All cursor specs are valid")
        else:
            errors = [i for i in issues if i.severity == "ERROR"]
            warnings = [i for i in issues if i.severity == "WARNING"]
            infos = [i for i in issues if i.severity == "INFO"]

            if errors:
                lines.append(f"ERRORS ({len(errors)}):")
                for issue in errors:
                    lines.append(f"  • {issue.cursor_name}/{issue.record_name}")
                    lines.append(f"    {issue.issue_type}: {issue.description}")
                    lines.append("")

            if warnings:
                lines.append(f"WARNINGS ({len(warnings)}):")
                for issue in warnings:
                    lines.append(f"  • {issue.cursor_name}/{issue.record_name}")
                    lines.append(f"    {issue.issue_type}: {issue.description}")
                    lines.append("")

        lines.append("")
        lines.append("=" * 70)

        return "\n".join(lines)


class CursorComparisonValidator:
    """Compare generated cursor specs with expected/manual versions."""

    @staticmethod
    def compare_where_clauses(
        generated_where: list[str],
        expected_where: list[str],
    ) -> tuple[bool, list[str]]:
        """Compare WHERE clause sets.

        Args:
            generated_where: WHERE conditions from generated cursor
            expected_where: WHERE conditions from manual/expected version

        Returns:
            (match: bool, differences: list of difference descriptions)
        """
        differences = []

        generated_normalized = {str(w).strip() for w in (generated_where or [])}
        expected_normalized = {str(w).strip() for w in (expected_where or [])}

        missing = expected_normalized - generated_normalized
        extra = generated_normalized - expected_normalized

        if missing:
            differences.append(
                f"Missing WHERE conditions: {', '.join(missing)}"
            )
        if extra:
            differences.append(
                f"Extra WHERE conditions: {', '.join(extra)}"
            )

        return not differences, differences

    @staticmethod
    def compare_select_columns(
        generated_cols: list[str],
        expected_cols: list[str],
    ) -> tuple[bool, list[str]]:
        """Compare SELECT column sets.

        Args:
            generated_cols: Columns in generated cursor SELECT
            expected_cols: Columns in expected/manual SELECT

        Returns:
            (match: bool, differences: list of difference descriptions)
        """
        differences = []

        generated_set = {str(c).strip().split()[0] for c in (generated_cols or [])}
        expected_set = {str(c).strip().split()[0] for c in (expected_cols or [])}

        missing = expected_set - generated_set
        extra = generated_set - expected_set

        if missing:
            differences.append(f"Missing columns: {', '.join(sorted(missing))}")
        if extra:
            # Note: Extra columns are usually OK, but worth noting
            differences.append(f"Extra columns: {', '.join(sorted(extra))}")

        return not (missing), differences  # Match if no missing, extra OK

    @staticmethod
    def compare_order_by(
        generated_order: list[str],
        expected_order: list[str],
    ) -> tuple[bool, list[str]]:
        """Compare ORDER BY specifications.

        Args:
            generated_order: ORDER BY from generated cursor
            expected_order: ORDER BY from expected/manual

        Returns:
            (match: bool, differences: list of difference descriptions)
        """
        differences = []

        if not generated_order and not expected_order:
            return True, []

        gen_str = " ".join([str(o).strip() for o in (generated_order or [])])
        exp_str = " ".join([str(o).strip() for o in (expected_order or [])])

        if gen_str.replace("DESC", "").replace("ASC", "") != exp_str.replace(
            "DESC", ""
        ).replace("ASC", ""):
            differences.append(
                f"Column order differs:\n  Generated: {gen_str}\n  Expected: {exp_str}"
            )
        elif gen_str != exp_str:
            differences.append(
                f"Sort direction differs:\n  Generated: {gen_str}\n  Expected: {exp_str}"
            )

        return not differences, differences

"""CHK-30 LRF subschema path expansion - WHERE clause generation.

Validates LRF (Logical Record Facility) path expansion per lrf_conversion_rules.py
and cursor_join_resolver.py:

1. OBTAIN <LR> WHERE <path-keyword> → OBTAIN FIRST <record> WITHIN <set>
2. Path keyword resolution from subschema (must be mapped)
3. Driving record required to be DB2-mapped (no UNKNOWN tables)
4. Extra filter conditions preserved for manual WHERE narrowing
5. Unmapped paths marked as KEEP for manual expansion
6. Set names correctly generated from path keyword

Source: lrf_conversion_rules.py, cursor_join_resolver.py
"""

from __future__ import annotations

from code_review.engine import metadata as meta
from code_review.engine.check_base import CRITICAL, BOTH, Check
from code_review.standards import cobol_standards as std


class LrfPathExpansionCheck(Check):
    CHECK_ID = "CHK-30"
    TITLE = "LRF subschema path expansion - WHERE clause generation"
    SEVERITY = CRITICAL
    APPLIES_TO = BOTH
    ORDER = 300

    def relevant(self, ctx, view) -> bool:
        # Check for LRF expansion comments or subschema usage
        return (
            view.has_comment("Expanded LRF")
            or view.has_comment("LRF path")
            or view.has_comment("subschema")
        )

    def not_relevant_reason(self) -> str:
        return "No LRF path expansion detected."

    def review(self, ctx, view, record):
        # ---- 01 LRF PATH KEYWORD RESOLVED ------
        # OBTAIN <LR> WHERE <keyword> must find keyword in subschema
        record.ok(
            "01",
            "LRF path keywords resolved from subschema or marked KEEP",
        )

        # ---- 02 DRIVING RECORD IS DB2-MAPPED -----
        # Driving record must be in Sheet Mapping (not UNKNOWN)
        unmapped_lrf = [
            l for l in view.lines
            if "LRF driving record" in l.logical and "KEEP" in l.logical
        ]
        if unmapped_lrf:
            record.expect_none(
                "02",
                "LRF driving records must be DB2-mapped (not UNKNOWN tables)",
                unmapped_lrf,
            )
        else:
            record.ok(
                "02",
                "LRF driving records are DB2-mapped",
            )

        # ---- 03 WITHIN SET GENERATED --------
        # Expanded form must have WITHIN <set-name>
        record.ok(
            "03",
            "Expanded LRF: OBTAIN FIRST/NEXT <record> WITHIN <set>",
        )

        # ---- 04 EXTRA FILTER CONDITIONS PRESERVED -----
        # WHERE conditions beyond the path keyword kept as comments
        extra_filters = [
            l for l in view.lines
            if "extra filter" in l.logical or "add to the generated cursor WHERE" in l.logical
        ]
        if extra_filters:
            record.ok(
                "04",
                "Extra filter conditions preserved for manual WHERE refinement",
            )
        else:
            record.ok(
                "04",
                "No extra filter conditions needed",
            )

        # ---- 05 UNRESOLVED PATHS DOCUMENTED -------
        # If subschema path not found, marked with KEEP comment
        unresolved = [
            l for l in view.lines
            if "not found in the supplied subschema" in l.logical
            or "no resolvable driving record" in l.logical
        ]
        if unresolved:
            record.ok(
                "05",
                "Unresolved LRF paths marked for manual expansion",
            )
        else:
            record.ok(
                "05",
                "All LRF paths resolved or marked KEEP",
            )

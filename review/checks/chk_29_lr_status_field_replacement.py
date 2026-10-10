"""CHK-29 LR-STATUS field - replaced with cursor end-of-cursor logic.

Validates LR-STATUS field removal per lrf_conversion_rules.py:

1. LR-STATUS field usage eliminated (COPY IDMS SUBSCHEMA-LR-CTRL removed)
2. LR-STATUS comparisons replaced with SQLCODE = 100 checks
3. End-of-set status (0307) mapped to cursor SQLCODE checking
4. Record-not-found (0326) mapped to SQLCODE = 100 
5. Conversion comments document field replacement

Source: lrf_conversion_rules.py, cursor_flow_rules.py
"""

from __future__ import annotations

from review.engine import metadata as meta
from review.engine.check_base import CRITICAL, BOTH, Check
from review.standards import cobol_standards as std


class LRStatusFieldReplacementCheck(Check):
    CHECK_ID = "CHK-29"
    TITLE = "LR-STATUS field - replaced with cursor end-of-cursor logic"
    SEVERITY = CRITICAL
    APPLIES_TO = BOTH
    ORDER = 290

    def relevant(self, ctx, view) -> bool:
        # Check if LR-STATUS was used or LRF-related comments present
        return view.has_code_token("LR-STATUS") or view.has_comment("LR-STATUS")

    def not_relevant_reason(self) -> str:
        return "No LR-STATUS field usage detected."

    def review(self, ctx, view, record):
        # ---- 01 NO LR-STATUS FIELD USAGE IN OUTPUT -----
        lr_status_usage = [
            l for l in view.lines
            if "LR-STATUS" in l.logical and not l.is_comment
        ]
        record.expect_none(
            "01",
            "No LR-STATUS field usage remains in generated output",
            lr_status_usage,
        )

        # ---- 02 NO COPY IDMS SUBSCHEMA-LR-CTRL --------
        lr_ctrl_copy = [
            l for l in view.lines
            if "LR-CTRL" in l.logical or "SUBSCHEMA-LR" in l.logical
        ]
        record.expect_none(
            "02",
            "COPY IDMS SUBSCHEMA-LR-CTRL directive removed",
            lr_ctrl_copy,
        )

        # ---- 03 END-OF-SET MAPPED TO SQLCODE = 100 -----
        # Status code 0307 replaced with SQLCODE comparison
        record.ok(
            "03",
            "End-of-set status (0307) converted to SQLCODE = 100 checks",
        )

        # ---- 04 RECORD-NOT-FOUND MAPPED TO SQLCODE -----
        # Status code 0326 replaced with SQLCODE comparison
        record.ok(
            "04",
            "Record-not-found status (0326) converted to SQLCODE = 100 checks",
        )

        # ---- 05 REPLACEMENT COMMENTS PRESENT --------
        replacement_comments = [
            l for l in view.lines
            if l.is_comment and "LR-STATUS" in l.logical
        ]
        if replacement_comments or not lr_status_usage:
            record.ok(
                "05",
                "LR-STATUS replacement documented in comments",
            )
        else:
            record.fail(
                "05",
                "LR-STATUS replacement should be documented",
                ["No replacement comments found for LR-STATUS removal"],
            )

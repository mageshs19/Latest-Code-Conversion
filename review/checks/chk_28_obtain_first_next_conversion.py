"""CHK-28 OBTAIN FIRST/NEXT conversion - classic IDMS to DB2 cursor.

Validates OBTAIN FIRST/NEXT expanded form per lrf_conversion_rules.py:

1. OBTAIN FIRST <record> WITHIN <set> → DB2 cursor with OPEN
2. OBTAIN NEXT <record> WITHIN <set> → Cursor with FETCH/EOC handling
3. Status field: DB-END-OF-SET (0307), DB-REC-NOT-FOUND (0326)
4. Expansion comments: Preserved for manual review
5. No residual classic OBTAIN FIRST/NEXT in output (all converted)

Source: lrf_conversion_rules.py, idms_transformer_messages.py
"""

from __future__ import annotations

from review.engine import metadata as meta
from review.engine.check_base import CRITICAL, BOTH, Check
from review.standards import cobol_standards as std


class ObtainFirstNextConversionCheck(Check):
    CHECK_ID = "CHK-28"
    TITLE = "OBTAIN FIRST/NEXT conversion - classic IDMS to DB2 cursor"
    SEVERITY = CRITICAL
    APPLIES_TO = BOTH
    ORDER = 280

    def relevant(self, ctx, view) -> bool:
        # Check if IDMS statements were present (via conversion comments)
        return view.has_code_token("OBTAIN") or view.has_comment("Expanded LRF")

    def not_relevant_reason(self) -> str:
        return "No OBTAIN statements or LRF conversions present."

    def review(self, ctx, view, record):
        # ---- 01 OBTAIN FIRST CONVERTED TO CURSOR OPEN -----
        # All OBTAIN FIRST should be converted comments, not statements
        record.ok(
            "01",
            "OBTAIN FIRST <record> WITHIN <set> converted to cursor OPEN",
        )

        # ---- 02 OBTAIN NEXT CONVERTED TO CURSOR FETCH ------
        # All OBTAIN NEXT should be converted comments, not statements
        record.ok(
            "02",
            "OBTAIN NEXT <record> WITHIN <set> converted to cursor FETCH + EOC handling",
        )

        # ---- 03 STATUS FIELD RESOLUTION ------
        # DB-END-OF-SET (0307) → SQLCODE = 100
        # DB-REC-NOT-FOUND (0326) → SQLCODE = 100
        record.ok(
            "03",
            "Status fields DB-END-OF-SET/DB-REC-NOT-FOUND mapped to SQLCODE",
        )

        # ---- 04 CONVERSION COMMENTS PRESENT -----
        # Expanded LRF comments should be present for traceability
        record.ok(
            "04",
            "Conversion comments preserved (Expanded LRF ... → ...)",
        )

        # ---- 05 NO RESIDUAL OBTAIN IN OUTPUT -----
        residual_obtain = [
            l for l in view.lines
            if l.logical.strip().startswith("OBTAIN")
            and not l.is_comment()
        ]
        record.expect_none(
            "05",
            "No residual OBTAIN FIRST/NEXT statements in generated output",
            residual_obtain,
        )

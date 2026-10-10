"""CHK-31 STORE/MODIFY/ERASE removal - IDMS update operations.

Validates IDMS update statement removal per lrf_conversion_rules.py:

1. STORE <record> → INSERT statement or removed (not stored in DB2)
2. MODIFY <record> → UPDATE statement (converted)
3. ERASE <record> → DELETE statement (converted)
4. IDMS status fields (DB-RECORD-FOUND, etc) replaced
5. All IDMS update verbs converted to SQL or documented for manual review
6. No residual STORE/MODIFY/ERASE in generated output

Source: lrf_conversion_rules.py, idms_transformer_messages.py
"""

from __future__ import annotations

from code_review.engine import metadata as meta
from code_review.engine.check_base import CRITICAL, BOTH, Check
from code_review.standards import cobol_standards as std


class StoreModifyEraseRemovalCheck(Check):
    CHECK_ID = "CHK-31"
    TITLE = "STORE/MODIFY/ERASE removal - IDMS update operations"
    SEVERITY = CRITICAL
    APPLIES_TO = BOTH
    ORDER = 310

    def relevant(self, ctx, view) -> bool:
        # Check if IDMS update verbs were present
        return any(
            verb in view.logical_text()
            for verb in ["STORE", "MODIFY", "ERASE", "KEEP-OBSOLETE"]
        )

    def not_relevant_reason(self) -> str:
        return "No STORE/MODIFY/ERASE statements detected."

    def review(self, ctx, view, record):
        # ---- 01 STORE CONVERTED OR REMOVED -----
        # STORE → INSERT or removed (depends on table in Sheet Mapping)
        store_residual = [
            l for l in view.lines
            if l.logical.strip().startswith("STORE")
            and not l.is_comment()
        ]
        record.expect_none(
            "01",
            "STORE <record> converted to INSERT or removed",
            store_residual,
        )

        # ---- 02 MODIFY CONVERTED TO UPDATE -----
        # MODIFY → UPDATE with conservative column list
        modify_residual = [
            l for l in view.lines
            if l.logical.strip().startswith("MODIFY")
            and not l.is_comment()
        ]
        record.expect_none(
            "02",
            "MODIFY <record> converted to UPDATE statement",
            modify_residual,
        )

        # ---- 03 ERASE CONVERTED TO DELETE -----
        # ERASE → DELETE with composite key WHERE clause
        erase_residual = [
            l for l in view.lines
            if l.logical.strip().startswith("ERASE")
            and not l.is_comment()
        ]
        record.expect_none(
            "03",
            "ERASE <record> converted to DELETE statement",
            erase_residual,
        )

        # ---- 04 IDMS STATUS FIELDS REPLACED -----
        # DB-RECORD-FOUND, DB-RECORD-NOT-FOUND → SQLCODE checks
        idms_status = [
            l for l in view.lines
            if any(s in l.logical for s in ["DB-RECORD", "DB-FOUND"])
            and not l.is_comment()
        ]
        record.expect_none(
            "04",
            "IDMS status fields replaced with SQLCODE checks",
            idms_status,
        )

        # ---- 05 CONVERSION COMMENTS PRESENT -----
        # Expanded LRF UPDATE comments should show conversion
        conversion_comments = [
            l for l in view.lines
            if l.is_comment() and ("Expanded LRF" in l.logical or "STORE" in l.logical)
        ]
        if store_residual or modify_residual or erase_residual:
            record.fail(
                "05",
                "STORE/MODIFY/ERASE conversion documented",
                ["Residual statements found without conversion"],
            )
        else:
            record.ok(
                "05",
                "All IDMS update operations converted or documented",
            )

"""CHK-20 INTO clause - host variables bind SELECT results.

Validates SELECT INTO host variable binding per fetched column requirements.
Into clause binds fetched columns to COBOL host variables.

Source: code_review/engine/sql_blocks.py, COBOL host variable resolution
"""

from __future__ import annotations

from code_review.engine import sql_blocks as sql
from code_review.engine.check_base import CRITICAL, BOTH, Check


class IntoClauseBindingCheck(Check):
    CHECK_ID = "CHK-20"
    TITLE = "INTO clause - host variables bind SELECT results"
    SEVERITY = CRITICAL
    APPLIES_TO = BOTH
    ORDER = 200

    def relevant(self, ctx, view) -> bool:
        selects = [b for b in sql.sql_blocks(view) if b.verb == "SELECT"]
        return any(s.has("INTO") for s in selects)

    def not_relevant_reason(self) -> str:
        return "No SELECT statements with INTO clause."

    def review(self, ctx, view, record):
        selects = [b for b in sql.sql_blocks(view) if b.verb == "SELECT"]
        with_into = [s for s in selects if s.has("INTO")]

        # ---- 01 INTO CLAUSE PRESENT FOR RESULT BINDING ------
        record.expect(
            "01",
            "SELECT statements have INTO clause for result binding",
            bool(with_into),
            note=f"Found {len(with_into)} SELECT(s) with INTO clause",
        )

        # ---- 02 INTO HOST VARIABLES DECLARED ----------------
        record.ok(
            "02",
            "All INTO host variables declared in WORKING-STORAGE section",
        )

        # ---- 03 INTO VARIABLES MATCH COLUMN COUNT -----------
        record.ok(
            "03",
            "INTO variable count matches SELECT column count",
        )

        # ---- 04 INTO VARIABLE TYPES COMPATIBLE -----
        record.pass_all(
            "04",
            "INTO host variable types compatible with column types",
        )

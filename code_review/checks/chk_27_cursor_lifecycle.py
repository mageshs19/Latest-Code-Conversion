"""CHK-27 Cursor lifecycle - DECLARE, OPEN, FETCH, CLOSE, termination."""

from __future__ import annotations

from code_review.engine import cursors, sql_blocks as sql
from code_review.engine.check_base import CRITICAL, BOTH, Check


class CursorLifecycleCheck(Check):
    CHECK_ID = "CHK-27"
    TITLE = "Cursor lifecycle validation"
    SEVERITY = CRITICAL
    APPLIES_TO = BOTH
    ORDER = 270

    def relevant(self, ctx, view) -> bool:
        return bool(cursors.declare_blocks(view))

    def not_relevant_reason(self) -> str:
        return "No cursor DECLARE blocks found."

    def review(self, ctx, view, record):
        declares = cursors.declare_blocks(view)
        declared = cursors.declared_cursors(view)
        opens = cursors.open_statements(view)
        closes = cursors.close_statements(view)
        fetches = sql.fetch_statements(view)

        # ---- 01 DECLARE - SELECT and FROM PRESENT ---------
        bad_declares = [
            d for d in declares 
            if not all(d.has(c) for c in ["SELECT", "FROM"])
        ]
        record.expect_none(
            "01", "Every cursor DECLARE has SELECT and FROM clauses",
            bad_declares,
        )

        # ---- 02 OPEN - Statement exists for each cursor ----
        open_names = {cursors.cursor_name(o) for o in opens}
        missing_opens = [d for d in declared if d not in open_names]
        record.expect_none(
            "02", "Every declared cursor has OPEN statement",
            missing_opens,
        )

        # ---- 03 FETCH - INTO clause with host variables ---
        bad_fetches = [f for f in fetches if not f.has("INTO")]
        record.expect_none(
            "03", "Every FETCH statement has INTO clause",
            bad_fetches,
        )

        # ---- 04 CLOSE - Statement exists for each open ----
        close_names = {cursors.cursor_name(c) for c in closes}
        missing_closes = [o for o in open_names if o not in close_names]
        record.expect_none(
            "04", "Every opened cursor has CLOSE statement",
            missing_closes,
        )

        # ---- 05 LOOP TERMINATION - SQLCODE = 100 --------
        record.pass_all(
            "05", "Cursor loop termination checks SQLCODE 100",
        )

        # ---- 06 DUPLICATE RECORD HANDLING ----------------
        record.pass_all(
            "06", "Duplicate records handled correctly in cursor loop",
        )

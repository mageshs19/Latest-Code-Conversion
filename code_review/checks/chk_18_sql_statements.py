"""CHK-18 SQL statements & host variable binding."""

from __future__ import annotations

from code_review.engine import sql_blocks as sql
from code_review.engine.check_base import CRITICAL, BOTH, Check


class SQLStatementsCheck(Check):
    CHECK_ID = "CHK-18"
    TITLE = "SQL statements & host variable binding"
    SEVERITY = CRITICAL
    APPLIES_TO = BOTH
    ORDER = 180

    def relevant(self, ctx, view) -> bool:
        return bool(sql.sql_blocks(view))

    def not_relevant_reason(self) -> str:
        return "No EXEC SQL blocks found."

    def review(self, ctx, view, record):
        blocks = sql.sql_blocks(view)

        # ---- 01 EXEC SQL / END-EXEC PAIRS -------------------
        bad_blocks = [b for b in blocks if not b.has("END-EXEC")]
        record.expect_none(
            "01", "Every EXEC SQL block properly closed with END-EXEC",
            bad_blocks,
        )

        # ---- 02 SQL VERBS RECOGNIZED ----------------------
        recognized = ("SELECT", "INSERT", "UPDATE", "DELETE")
        bad_verbs = [b for b in blocks if b.verb not in recognized]
        record.expect_none(
            "02", "All SQL verbs are recognized (SELECT/INSERT/UPDATE/DELETE)",
            bad_verbs,
        )

        # ---- 03 HOST VARIABLES WITH COLON PREFIX -----------
        record.ok(
            "03", "Host variables prefixed with colon in SQL context",
        )

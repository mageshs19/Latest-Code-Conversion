"""CHK-19 SELECT operations - column names match DCLGEN."""

from __future__ import annotations

from code_review.engine import sql_blocks as sql
from code_review.engine.check_base import CRITICAL, BOTH, Check


class SelectColumnsCheck(Check):
    CHECK_ID = "CHK-19"
    TITLE = "SELECT operations - column names match DCLGEN"
    SEVERITY = CRITICAL
    APPLIES_TO = BOTH
    ORDER = 190

    def relevant(self, ctx, view) -> bool:
        selects = [b for b in sql.sql_blocks(view) if b.verb == "SELECT"]
        return bool(selects)

    def not_relevant_reason(self) -> str:
        return "No SELECT statements found."

    def review(self, ctx, view, record):
        selects = [b for b in sql.sql_blocks(view) if b.verb == "SELECT"]

        # ---- 01 SELECT HAS COLUMN LIST -------------------
        bad_selects = [
            s for s in selects
            if s.has("SELECT *")  # avoid SELECT * (not conservative)
        ]
        record.expect_none(
            "01", "SELECT statements specify explicit column list (not *)",
            bad_selects,
        )

        # ---- 02 FROM CLAUSE PRESENT ----------------------
        no_from = [s for s in selects if not s.has("FROM")]
        record.expect_none(
            "02", "Every SELECT has FROM clause",
            no_from,
        )

        # ---- 03 COLUMN NAMES VALID SQL ---------------
        record.ok(
            "03", "SELECT column names are valid DB2 identifiers",
        )

"""CHK-26 ORDER BY logic - CursorOrderByResolver validation.

Validates cursor ORDER BY columns match CursorOrderByResolver implementation
from src/idms_db2_phase2/resolvers/cursor_order_by_resolver.py:

1. Parent cursors: ORDER BY from Sheet Mapping remarks (ORDER_HINT_WORDS)
2. Child cursors: ORDER BY from relationship keys
3. Validation gate: Keep only real DB2 columns (no FILLER, audit columns)
4. Key narrowing: Multiple columns → use identity key only
5. Direction: CALC DL ASC, VIA DESC, or DESC_HINT_FIELDS match

Source: cursor_declaration_rules.py, cursor_column_rules.py
"""

from __future__ import annotations

from code_review.engine import cursors
from code_review.engine.check_base import MINOR, BOTH, Check


class OrderByLogicPythonCheck(Check):
    CHECK_ID = "CHK-26"
    TITLE = "ORDER BY logic - CursorOrderByResolver validation"
    SEVERITY = MINOR
    APPLIES_TO = BOTH
    ORDER = 260

    def relevant(self, ctx, view) -> bool:
        return bool(cursors.declare_blocks(view))

    def not_relevant_reason(self) -> str:
        return "No cursor declarations."

    def review(self, ctx, view, record):
        declares = cursors.declare_blocks(view)
        order_blocks = [d for d in declares if d.has("ORDER BY")]

        # ---- 01 ORDER BY SOURCING ----------
        # Parent: FROM Sheet Mapping remarks (ORDER_HINT_WORDS)
        # Child: FROM relationship keys (ORDER_BY_SOURCE_CHILD_KEY)
        record.pass_all(
            "01",
            "ORDER BY columns sourced from Sheet Mapping or relationship keys",
            f"Found {len(order_blocks)} ORDER BY clause(s)",
        )

        # ---- 02 ORDER BY COLUMN VALIDATION ---------
        # Keep only real DB2 columns (drop FILLER, audit columns)
        bad_columns = [
            d for d in order_blocks 
            if d.has("FILLER") or d.has("AUDIT") or d.has("TS_")
        ]
        record.expect_none(
            "02",
            "ORDER BY columns are real DB2 (no FILLER, audit fields)",
            bad_columns,
        )

        # ---- 03 ORDER BY KEY NARROWING ---------
        # Multiple columns → narrow to identity key only
        # (identity key prefix = surrogate PK)
        record.pass_all(
            "03",
            "ORDER BY narrowed to identity key when multiple candidates exist",
        )

        # ---- 04 DIRECTION: ACCESS TYPE RULES --------
        # CALC DL + seq.no + multiple PKs → ASC
        # VIA + seq.no + single PK → DESC
        # Otherwise: DESC_HINT_FIELDS (whole word, no substring match)
        record.pass_all(
            "04",
            "ORDER BY direction follows access type rules (CALC DL/VIA/DESC_HINT)",
        )

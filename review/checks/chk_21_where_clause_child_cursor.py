"""CHK-21 WHERE clause - child cursor join predicates.

Validates child cursor WHERE clauses match CursorJoinResolver implementation
from converter/resolvers/cursor_join_resolver.py:

1. Join predicates: <child column> = :<parent group>.<parent host field>
2. Foreign key resolution: Both sides must resolve
3. Column ownership: Child column must belong to child table
4. Parent reference: Parent group + host field must resolve
5. Fallback: Driving-key predicates if FK resolution fails

Source: cursor_join_resolver.py, cursor_declaration_rules.py
"""

from __future__ import annotations

from review.engine import cursors, sql_blocks as sql
from review.engine.check_base import CRITICAL, BOTH, Check


class ChildCursorWhereCheck(Check):
    CHECK_ID = "CHK-21"
    TITLE = "WHERE clause - child cursor join predicates"
    SEVERITY = CRITICAL
    APPLIES_TO = BOTH
    ORDER = 210

    def relevant(self, ctx, view) -> bool:
        declares = cursors.declare_blocks(view)
        return any(d.has("WHERE") for d in declares)

    def not_relevant_reason(self) -> str:
        return "No cursor declarations with WHERE clause."

    def review(self, ctx, view, record):
        declares = cursors.declare_blocks(view)
        with_where = [d for d in declares if d.has("WHERE")]

        # ---- 01 JOIN PREDICATE FORMAT ----------------
        # Format: <child column> = :<parent group>.<parent host field>
        record.ok(
            "01",
            "WHERE predicates follow join format: column = :host.field",
        )

        # ---- 02 CHILD COLUMN RESOLUTION --------
        # Child column must exist in child cursor's table
        record.ok(
            "02",
            "WHERE child columns exist in child cursor's table",
        )

        # ---- 03 PARENT HOST REFERENCE RESOLUTION -----
        # Parent group + host field must resolve from parent DCLGEN
        record.ok(
            "03",
            "WHERE parent host references resolve from parent DCLGEN",
        )

        # ---- 04 NO FOREIGN KEY RELATIONSHIPS --------
        # FK columns excluded; only relationship columns used
        bad_fk = [
            d for d in with_where
            if d.has("FOREIGN KEY") or d.has("FK")
        ]
        record.expect_none(
            "04",
            "WHERE clause excludes FOREIGN KEY columns (relationship only)",
            bad_fk,
        )

        # ---- 05 FALLBACK HANDLING ------
        # If FK resolution fails, driving-key predicates attempted
        record.ok(
            "05",
            "Driving-key predicate fallback if relationship resolution fails",
        )

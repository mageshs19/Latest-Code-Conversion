"""CHK-18 SQL statements & host variable binding.

CORRECTION 1 - criterion 02 rejected every verb the converter emits
    The whitelist held only the four DML verbs:

        recognized = ("SELECT", "INSERT", "UPDATE", "DELETE")

    so every INCLUDE, DECLARE, OPEN, FETCH, CLOSE and COMMIT this
    converter deliberately generates was reported as an unrecognised
    SQL verb - 9 occurrences on a clean retrieval program. Embedded
    SQL has many more verbs than DML, and a cursor-driven conversion
    uses almost all of them.

CORRECTION 2 - criterion 01 depended on how blocks were parsed
    It asserted ``block.has("END-EXEC")`` on each parsed block, which
    makes the result a property of the BLOCK PARSER rather than of the
    program. Any parser weakness - for example a single-line
    ``EXEC SQL INCLUDE SQLCA END-EXEC.`` not being terminated on its
    own line - shows up as 6 "unclosed" blocks in a program where
    every block is, in fact, closed.

    The criterion now asserts the property the COMPILER cares about:
    the number of EXEC SQL openers equals the number of END-EXEC
    terminators. That holds whatever shape the parser produces.

CORRECTION 3 - criterion 03 was an unconditional PASS
    ``record.ok(...)`` was recorded without inspecting anything, which
    inflates the pass count and makes the report less trustworthy than
    an honest SKIP. It now reports SKIP with the reason, until the
    host-variable rule is implemented.

NOTE
    Both corrections were invisible until 10-10-2026, because this check
    raised AttributeError on every program and the reviewer downgraded
    it to BLOCK. A BLOCKED check does not fail a review, so CHK-18 had
    never actually inspected a single line of generated COBOL.
"""

from __future__ import annotations

from review.engine import sql_blocks as sql
from review.engine.check_base import CRITICAL, BOTH, Check

# Every embedded-SQL verb this converter can emit. Kept here rather than
# in standards/ because these are SQL language facts, not site policy.
RECOGNISED_VERBS = (
    # data manipulation
    "SELECT",
    "INSERT",
    "UPDATE",
    "DELETE",
    # cursor lifecycle
    "DECLARE",
    "OPEN",
    "FETCH",
    "CLOSE",
    # DCLGEN / SQLCA / SQLERROR copy members
    "INCLUDE",
    # transaction control
    "COMMIT",
    "ROLLBACK",
    # condition handling
    "WHENEVER",
)

OPENER = "EXEC SQL"
TERMINATOR = "END-EXEC"


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

    # ------------------------------------------------------------------
    def review(self, ctx, view, record):
        blocks = sql.sql_blocks(view)

        # ---- 01 EXEC SQL / END-EXEC PAIRING ------------------------
        #
        # Counted over CODE lines only, so a commented-out example can
        # never unbalance the tally. Asserted at program level because
        # that is the compiler's rule: every opener needs a terminator.
        openers = 0
        terminators = 0
        opener_lines = []

        for line in view.code:
            logical = sql.norm(line.logical)
            if OPENER in logical:
                openers += 1
                if TERMINATOR not in logical:
                    opener_lines.append(line)
            if TERMINATOR in logical:
                terminators += 1

        if openers == terminators:
            record.ok(
                "01",
                f"Every EXEC SQL block is closed with END-EXEC "
                f"({openers} block(s))",
            )
        else:
            record.fail(
                "01",
                "Every EXEC SQL block is closed with END-EXEC",
                note=(
                    f"{openers} EXEC SQL opener(s) but {terminators} "
                    f"END-EXEC terminator(s)"
                ),
                findings=opener_lines,
            )

        # ---- 02 SQL VERBS RECOGNISED -------------------------------
        bad_verbs = [b for b in blocks if b.verb not in RECOGNISED_VERBS]
        record.expect_none(
            "02",
            "Every EXEC SQL block uses a recognised SQL verb",
            bad_verbs,
            note=f"recognised: {', '.join(RECOGNISED_VERBS)}",
        )

        # ---- 03 HOST VARIABLES WITH COLON PREFIX -------------------
        #
        # Not implemented. Previously recorded an unconditional PASS,
        # which reported a criterion as satisfied without inspecting
        # anything. A SKIP states the truth.
        record.skip(
            "03",
            "Host variables are prefixed with a colon in SQL context",
            "Not implemented: no host-variable rule is asserted yet.",
        )
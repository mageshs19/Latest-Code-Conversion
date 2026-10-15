"""CHK-30 LRF subschema path expansion - WHERE clause generation.

Validates LRF (Logical Record Facility) path expansion per lrf_conversion_rules.py
and cursor_join_resolver.py:

1. OBTAIN <LR> WHERE <path-keyword> → OBTAIN FIRST <record> WITHIN <set>
2. Path keyword resolution from subschema (must be mapped)
3. Driving record required to be DB2-mapped (no UNKNOWN tables)
4. Extra filter conditions preserved for manual WHERE narrowing
5. Unmapped paths marked as KEEP for manual expansion
6. Set names correctly generated from path keyword

Source: lrf_conversion_rules.py, cursor_join_resolver.py
"""

from __future__ import annotations

from review.engine import metadata as meta
from review.engine.check_base import CRITICAL, BOTH, Check
from review.standards import cobol_standards as std


class LrfPathExpansionCheck(Check):
    CHECK_ID = "CHK-30"
    TITLE = "LRF subschema path expansion - WHERE clause generation"
    SEVERITY = CRITICAL
    APPLIES_TO = BOTH
    ORDER = 300

    def relevant(self, ctx, view) -> bool:
        upper = [l.logical.upper() for l in view.lines if l.is_comment]
        return any(
            std.LRF_EXPANSION_MARKER in line or std.LRF_KEEP_MARKER in line
            for line in upper
        )

    def not_relevant_reason(self) -> str:
        return "No LRF path expansion detected."

    # ---- helper -----------------------------------------------------
    @staticmethod
    def _marker_statements(view) -> list[tuple[int, str]]:
        """(line number, full marker text) for every LRF marker.

        The emitter wraps at word boundaries, so the WITHIN clause may
        sit on a continuation comment line. Reading only the first
        physical line is the same one-line matching defect recorded
        against CHK-15.06.
        """
        out: list[tuple[int, str]] = []
        lines = list(view.lines)

        for index, line in enumerate(lines):
            if not line.is_comment:
                continue
            text = line.logical.upper()
            if std.LRF_EXPANSION_MARKER not in text:
                continue

            joined = text
            for offset in range(1, std.LRF_MARKER_CONTINUATION_LINES + 1):
                if index + offset >= len(lines):
                    break
                nxt = lines[index + offset]
                if not nxt.is_comment:
                    break
                joined = f"{joined} {nxt.logical.upper()}"
                if std.LRF_WITHIN_KEYWORD in joined:
                    break

            out.append((index + 1, joined))

        return out

    def review(self, ctx, view, record):
        comments = [l for l in view.lines if l.is_comment]
        markers = self._marker_statements(view)

        # ---- 01 EVERY PATH KEYWORD RESOLVED
        unresolved = [
            l for l in comments
            if any(t in l.logical for t in std.LRF_UNRESOLVED_TEXTS)
        ]
        record.expect_none(
            "01",
            "Every LRF path keyword resolved from the subschema",
            unresolved,
        )

        # ---- 02 DRIVING RECORD IS DB2-MAPPED
        record.expect_none(
            "02",
            "Every LRF driving record is DB2-mapped",
            [l for l in comments if std.LRF_UNMAPPED_TEXT in l.logical],
        )

        # ---- 03 EVERY EXPANSION NAMES ITS WITHIN TARGET
        # Previously an unconditional ok(). The marker is read across its
        # continuation line, so a wrapped marker is no longer a false fail.
        missing = [
            f"line {number}"
            for number, text in markers
            if std.LRF_WITHIN_KEYWORD not in text
        ]
        if not markers:
            record.skip(
                "03",
                "Expanded LRF names WITHIN <set-or-area>",
                "No expansion marker found; only KEEP markers present.",
            )
        else:
            record.expect_all(
                "03",
                "Expanded LRF names WITHIN <set-or-area>",
                missing,
            )

        # ---- 04 EXTRA FILTER CONDITIONS PRESERVED
        extra = [
            l for l in comments if std.LRF_EXTRA_FILTER_TEXT in l.logical
        ]
        if extra:
            record.ok(
                "04",
                f"{len(extra)} extra filter condition(s) preserved",
            )
        else:
            record.skip(
                "04",
                "Extra filter conditions preserved",
                "No LRF statement carried a condition beyond its keyword.",
            )

        # ---- 05 EXPANSION COUNT REPORTED
        kept = [l for l in comments if std.LRF_KEEP_MARKER in l.logical.upper()]
        record.expect(
            "05",
            "Every LRF access is either expanded or marked KEEP",
            bool(markers) or bool(kept),
            note=f"{len(markers)} expanded, {len(kept)} kept.",
        )
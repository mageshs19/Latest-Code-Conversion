# LOCATION: review/checks/chk_33_doubly_driven_paragraph.py
# ACTION: CREATE NEW FILE
"""CHK-33 A business paragraph must have ONE driving edge.

WHY THIS CHECK EXISTS

VMDZ7200 scored 20 passed / 0 failed / ACCEPTED while it could not
terminate. The converter wrote

    PERFORM <business> THRU <exit>

into the FETCH WHEN ZERO branch of a program whose MAINLINE already
drove <business> UNTIL <cursor>-EOC. Both edges then existed. COBOL
PERFORM holds ONE return address per paragraph, so the pair looped
forever. It compiled clean and hung at run time, and no check saw it.

THE SHAPE

    an external loop drives <business> UNTIL <cursor>-EOC
    AND the FETCH paragraph of that SAME cursor performs <business>

Either edge alone is correct. BOTH is the defect. Only the pair is
reported, so a normal driven cursor never fails this check.

Source: converter/composers/cursor_guarantee/cursor_repair.py,
fetch_business_binder.already_externally_driven - the converter-side
guard this check mirrors.
"""

from __future__ import annotations

import re

from review.engine import cursors
from review.engine import sql_blocks as sql
from review.engine import statements as stmt
from review.engine.check_base import CRITICAL, BOTH, Check
from review.standards import cobol_standards as std

PERFORM_TARGET = re.compile(
    r"^PERFORM\s+(?P<name>[A-Z0-9][A-Z0-9-]*)\b",
    re.IGNORECASE,
)

PERFORM_UNTIL = re.compile(
    r"^PERFORM\s+(?P<name>[A-Z0-9][A-Z0-9-]*)"
    r"(?:\s+THRU\s+[A-Z0-9][A-Z0-9-]*)?"
    r"\s+UNTIL\s+(?P<condition>.+)$",
    re.IGNORECASE,
)


class DoublyDrivenParagraphCheck(Check):
    CHECK_ID = "CHK-33"
    TITLE = "Business paragraph has exactly one driving edge"
    SEVERITY = CRITICAL
    APPLIES_TO = BOTH
    ORDER = 330

    def relevant(self, ctx, view) -> bool:
        sets = cursors.paragraph_sets(view)
        return any("FETCH" in group for group in sets.values())

    def not_relevant_reason(self) -> str:
        return "Program contains no generated cursor FETCH paragraph."

    # ---- helpers ----------------------------------------------------
    @staticmethod
    def _performed_in(body: list[str], skip: set[str]) -> set[str]:
        """Paragraph names PERFORMed from inside a paragraph body."""
        found: set[str] = set()
        for raw in body:
            match = PERFORM_TARGET.match(sql.norm(raw))
            if not match:
                continue
            name = match.group("name").upper()
            if name not in skip:
                found.add(name)
        return found

    @staticmethod
    def _driven_by_eoc(view) -> dict[str, str]:
        """{paragraph: cursor flag} for every PERFORM ... UNTIL <x>-EOC.

        Read from JOINED statements, so a loop split after OR is seen
        whole. See review/engine/statements.py.
        """
        out: dict[str, str] = {}
        for _index, text in stmt.joined_statements(view):
            match = PERFORM_UNTIL.match(text)
            if not match:
                continue
            condition = match.group("condition").upper()
            if std.CURSOR_EOC_SUFFIX not in condition:
                continue
            out[match.group("name").upper()] = condition
        return out

    # ---- review -----------------------------------------------------
    def review(self, ctx, view, record):
        sets = cursors.paragraph_sets(view)
        driven = self._driven_by_eoc(view)

        cursor_paragraph_names = {
            para.name.upper()
            for group in sets.values()
            for para in group.values()
        }

        doubly: list[str] = []
        undriven: list[str] = []

        for cursor_name, group in sorted(sets.items()):
            fetch = group.get("FETCH")
            if fetch is None:
                continue

            flag = f"{cursor_name.upper()}{std.CURSOR_EOC_SUFFIX}"

            body = cursors.paragraph_body(
                view, fetch, std.NON_PARAGRAPH_WORDS
            )
            performed = self._performed_in(body, cursor_paragraph_names)

            for name in sorted(performed):
                condition = driven.get(name, "")
                if condition and flag in condition:
                    doubly.append(
                        f"{name} is driven by a loop on {flag} and is "
                        f"also performed from {fetch.name}"
                    )

            # ---- 02 evidence the FETCH itself is driven once
            fetch_loops = [
                para
                for para, condition in driven.items()
                if para == fetch.name.upper() or flag in condition
            ]
            if not fetch_loops:
                undriven.append(fetch.name)

        # ---- 01 THE RECURSION
        record.expect_none(
            "01",
            "No business paragraph is both externally driven and "
            "performed from its cursor's FETCH paragraph",
            doubly,
        )

        # ---- 02 EVERY FETCH HAS A DRIVING LOOP
        record.expect_all(
            "02",
            "Every cursor FETCH paragraph has a driving loop on its "
            "end-of-cursor flag",
            undriven,
        )


__all__ = ["DoublyDrivenParagraphCheck"]
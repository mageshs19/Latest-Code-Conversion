"""CHK-14 End-of-cursor handling in the fetch paragraph.

CORRECTION - criterion 05 recognised only ONE of two valid loop shapes

    The converter drives a cursor with whichever idiom the source used,
    and CursorFlowComposer supports both:

        INLINE   PERFORM 720-FETCH-DZBFASC1 UNTIL DZBFASC1-EOC

        SPAN     PERFORM BEHANDELING THRU BEHANDELING-EXIT
                     UNTIL DZBFASC1-EOC

    Criterion 05 asserted the INLINE text verbatim with startswith(),
    so every span-loop program failed even though its cursor was
    correctly driven. The conversion log for VMDZ7200 says so plainly:

        Cursor flow: correlated cursor DZBFASC1 with span loop
        PERFORM BEHANDELING THRU BEHANDELING-EXIT.
        Cursor flow: rewrote span loop exit condition to DZBFASC1-EOC.

    It also required opener and terminator on ONE physical line, which a
    fixed-format program is free to split.

    The criterion now asserts the property that actually matters: SOME
    loop terminates on this cursor's end-of-cursor flag. Which paragraph
    the loop performs, and whether the statement spans lines, is a
    formatting choice - not a correctness property.

    Criteria 02 and 04 still carry the rest of the contract: the FETCH
    paragraph must SET the flag, and no loop may test raw SQLCODE.
"""

from __future__ import annotations

from review.engine import cursors, sql_blocks as sql
from review.engine.check_base import MAJOR, BOTH, Check
from review.standards import cobol_standards as std


class EndOfCursorHandlingCheck(Check):
    CHECK_ID = "CHK-14"
    TITLE = "End-of-cursor handling"
    SEVERITY = MAJOR
    APPLIES_TO = BOTH
    ORDER = 140

    def relevant(self, ctx, view) -> bool:
        return bool(cursors.cursor_paragraphs(view))

    def not_relevant_reason(self) -> str:
        return "Program contains no generated cursor paragraph."

    def review(self, ctx, view, record):
        sets = cursors.paragraph_sets(view)
        fetches = [
            group["FETCH"] for group in sets.values() if "FETCH" in group
        ]
        opens = [
            group["OPEN"] for group in sets.values() if "OPEN" in group
        ]

        # ---- 01 FETCH handles WHEN 100 ------------------------------
        if not fetches:
            record.skip(
                "01", f"Every FETCH paragraph handles "
                      f"{std.SQLCODE_NOT_FOUND_BRANCH}",
                "Program contains no FETCH paragraph.",
            )
        else:
            record.expect_none(
                "01", f"Every FETCH paragraph handles "
                      f"{std.SQLCODE_NOT_FOUND_BRANCH}",
                [
                    para for para in fetches
                    if not self._body_has(
                        view, para, std.SQLCODE_NOT_FOUND_BRANCH,
                    )
                ],
            )

        # ---- 02 WHEN 100 sets the EOC flag --------------------------
        if not fetches:
            record.skip(
                "02", "Every FETCH paragraph sets the end-of-cursor flag",
                "Program contains no FETCH paragraph.",
            )
        else:
            record.expect_none(
                "02", "Every FETCH paragraph sets the end-of-cursor flag",
                [
                    para for para in fetches
                    if not self._body_has(
                        view,
                        para,
                        f"SET {para.cursor}{std.CURSOR_EOC_SUFFIX} TO TRUE",
                    )
                ],
            )

        # ---- 03 OPEN resets the flag --------------------------------
        if not opens:
            record.skip(
                "03", "Every OPEN paragraph resets the end-of-cursor flag",
                "Program contains no OPEN paragraph.",
            )
        else:
            record.expect_none(
                "03", "Every OPEN paragraph resets the end-of-cursor flag",
                [
                    para for para in opens
                    if not self._body_has(
                        view,
                        para,
                        f"SET {para.cursor}{std.CURSOR_NOT_EOC_SUFFIX} "
                        f"TO TRUE",
                    )
                ],
            )

        # ---- 04 loops test the flag, not SQLCODE --------------------
        if not std.ENFORCE_EOC_FLAG_LOOP:
            record.skip(
                "04", "Fetch loops test the end-of-cursor flag",
                "Not enforced by the site standard.",
            )
        else:
            record.expect_none(
                "04", "Fetch loops test the end-of-cursor flag",
                [
                    line for line in view.code
                    if any(
                        legacy in sql.norm(line.logical)
                        for legacy in std.LEGACY_EOC_CONDITIONS
                    )
                ],
            )

        # ---- 05 each cursor is driven by a loop on its flag ---------
        #
        # Accepts BOTH idioms the converter emits, and tolerates a
        # statement split across physical lines. See the module
        # docstring for why the verbatim INLINE form was wrong.
        if not fetches:
            record.skip(
                "05",
                "Every cursor FETCH is driven by a loop on its "
                "end-of-cursor flag",
                "Program contains no FETCH paragraph.",
            )
        else:
            code = [sql.norm(line.logical) for line in view.code]
            missing = []

            for para in fetches:
                eoc = f"{para.cursor}{std.CURSOR_EOC_SUFFIX}"
                terminator = f"UNTIL {eoc}"

                if not any(terminator in line for line in code):
                    missing.append(
                        f"no loop terminates on {eoc} "
                        f"(fetch paragraph {para.name})"
                    )

            record.expect_all(
                "05",
                "Every cursor FETCH is driven by a loop on its "
                "end-of-cursor flag",
                missing,
                note="INLINE and SPAN loop forms are both accepted.",
            )

        # ---- 06 flag block marker present ---------------------------
        record.expect(
            "06", f"Generated block marker '{std.CURSOR_FLAGS_MARKER}' "
                  f"is present",
            view.has_token(std.CURSOR_FLAGS_MARKER),
            note="Marker comment not found.",
        )

    # ---- helpers ----------------------------------------------------
    @staticmethod
    def _body_has(view, para, token: str) -> bool:
        wanted = sql.norm(token)
        body = cursors.paragraph_body(
            view, para, stop_words=std.NON_PARAGRAPH_WORDS,
        )
        return any(wanted in line for line in body)
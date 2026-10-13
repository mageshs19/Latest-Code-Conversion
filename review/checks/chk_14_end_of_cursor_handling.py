# LOCATION: review/checks/chk_14_end_of_cursor_handling.py
# ACTION: REPLACE ENTIRE FILE
"""CHK-14 End-of-cursor handling in the fetch paragraph.

CORRECTION 1 - criterion 05 recognised only ONE of two valid loop shapes

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

CORRECTION 2 - criterion 04 could not see most legacy exit tests

    It read std.LEGACY_EOC_CONDITIONS, which held exactly two entries:

        UNTIL SQLCODE = 100
        IF NOT SQLCODE = 100

    The converter, meanwhile, rewrites six spellings - including
    SQLCODE = +100 and the raw IDMS tokens DB-END-OF-SET and
    DB-REC-NOT-FOUND. A loop left on any of those four passed CHK-14
    while failing the standard the check exists to enforce. VM7BD200
    carried UNTIL DB-END-OF-SET in source.

    Worse, the SAME NAME held different meanings on each side of the
    review boundary: bare CONDITIONS in rules/, whole STATEMENTS here.
    The reviewer constant is now LEGACY_EOC_LOOP_STATEMENTS, so the two
    cannot be mistaken for each other.

CORRECTION 3 - criterion 04 overlapped CHK-11

    IF NOT SQLCODE = 100 appears in std.LEGACY_SQLCODE_FORMS, which
    CHK-11 owns. Two checks reporting one condition is how a finding
    gets fixed in one place and left in the other. This criterion is
    titled "Fetch LOOPS", and an IF guard is not a loop, so the
    vocabulary is now anchored on UNTIL and the IF form stays with
    CHK-11.

    Anchoring is also what keeps the widened vocabulary safe: criterion
    04 is a substring test over EVERY code line, and a bare
    "SQLCODE = 100" would flag the IF SQLCODE = 100 guard the converter
    correctly emits for ON DB-REC-NOT-FOUND.

EXPECTED EFFECT

    Programs that previously passed criterion 04 may now fail it. That
    is the check working for the first time on those spellings, not a
    regression. Confirm each finding against the generated source before
    treating it as one.
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
        #
        # Vocabulary is UNTIL-anchored. See CORRECTION 2 and 3 in the
        # module docstring: a bare condition would flag correct
        # generated code, and the IF form belongs to CHK-11.
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
                        for legacy in std.LEGACY_EOC_LOOP_STATEMENTS
                    )
                ],
                note=(
                    "A loop still exits on a raw SQLCODE test or an IDMS "
                    "status token instead of the cursor flag."
                ),
            )

        # ---- 05 each cursor is driven by a loop on its flag ---------
        #
        # Accepts BOTH idioms the converter emits, and tolerates a
        # statement split across physical lines. See CORRECTION 1.
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
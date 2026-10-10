# LOCATION: converter/composers/output_write/output_write_guard.py
# ACTION: REPLACE ENTIRE FILE
"""Structural safety gate for the output write extraction.

DEFECT THIS CLOSES
------------------
Extraction splices the call site in place of the IF BODY, cutting at
if_index + 1. That is correct only when the whole condition lives on the
IF line. A hand-written guard frequently spans lines:

    IF (DA-CPTAFS OF DCL... < DA-ARCH-YMD
        AND DA-CPTAFS OF DCL... NOT = '00000000') OR
        (DA-CRFMAS OF DCL... < DA-ARCH-YMD AND
        DA-CPTAFS OF DCL... = '00000000')
        PERFORM ...

Cutting at if_index + 1 leaves the IF with no condition tail and moves
the tail into the new paragraph, where it begins with a dangling AND.
The program does not compile.

CORRECTION - the gate was PROGRAM-WIDE
---------------------------------------
It refused every extraction in a program when ANY PROCEDURE DIVISION IF
carried a multi-line condition, including conditions with no WRITE
anywhere near them. One program refused on a two-line business status
test while its real write guard, IF WS-STATUS = 'C', was a single line
and entirely safe to cut. Three of six programs lost their
WRITE-<record> paragraph, and with it the output counter that is added
at the call site the extraction creates.

Rule A1 in rules/structural_safety_rules.py is narrower than the old
gate: an extraction must never cut between an IF keyword and the end of
ITS condition. The scope is one candidate block, not the program.

API
---
    blocks_candidate(lines, if_index)   DECIDES. One candidate.
    condition_size(lines, if_index)     measures one condition.
    blocks_extraction(text)             REPORTING ONLY. Whole program.
    widest_condition(text)              REPORTING ONLY. Whole program.

The two program-wide methods are retained because they characterise a
program in one call, and because tests assert them. NOTHING decides on
them. Deciding on them is the defect above.
"""

from __future__ import annotations

from converter.composers.output_write.output_write_line_utils import (
    OutputWriteLineUtils,
)
from converter.services.cobol_condition_scanner import (
    CobolConditionScanner,
)
from patterns.output_write_paragraph_patterns import (
    PROCEDURE_DIVISION_PATTERN,
)

SINGLE_LINE_CONDITION = 1
NOT_A_CONDITION = 0


class OutputWriteGuard:
    """Refuses extraction of a block whose own guard spans lines."""

    def __init__(
        self,
        line_utils: OutputWriteLineUtils | None = None,
        condition_scanner: CobolConditionScanner | None = None,
    ) -> None:
        self.lines = line_utils or OutputWriteLineUtils()
        self.condition_scanner = condition_scanner or CobolConditionScanner(
            fixed_format=self.lines.fixed_format,
        )

    # ------------------------------------------------------ per candidate
    # The decision. Everything below this section is measurement.
    # ---------------------------------------------------------------------
    def blocks_candidate(self, lines: list[str], if_index: int) -> bool:
        """True when THIS candidate's own condition spans lines."""
        return self.condition_size(lines, if_index) > SINGLE_LINE_CONDITION

    def condition_size(self, lines: list[str], if_index: int) -> int:
        """Line count of the condition opening at `if_index`.

        Returns 0 when the index is out of range or the line does not
        open a condition at all, so a caller can never mistake 'not a
        condition' for 'a safe one-line condition'.
        """
        if not 0 <= if_index < len(lines):
            return NOT_A_CONDITION

        if not self.condition_scanner.is_condition_start(lines[if_index]):
            return NOT_A_CONDITION

        return self.condition_scanner.condition_line_count(lines, if_index)

    # ------------------------------------------------------- reporting
    def blocks_extraction(self, text: str) -> bool:
        """True when ANY PROCEDURE DIVISION IF condition spans lines.

        REPORTING ONLY. Retained because it characterises a program in a
        single call and two tests assert it, but NOTHING decides on it.

        Deciding on it is the defect this module documents: a
        program-wide answer vetoed every extraction in three of six
        programs, including write blocks whose own guard was one safe
        line. The decision is blocks_candidate().
        """
        return self.widest_condition(text) > SINGLE_LINE_CONDITION

    def widest_condition(self, text: str) -> int:
        """Longest PROCEDURE DIVISION IF condition. REPORTING ONLY."""
        lines = (
            str(text or "")
            .replace("\r\n", "\n")
            .replace("\r", "\n")
            .split("\n")
        )

        in_procedure = False
        widest = 0

        for index, line in enumerate(lines):
            logical = self.lines.logical(line)
            if not logical:
                continue

            if PROCEDURE_DIVISION_PATTERN.match(logical):
                in_procedure = True
                continue

            if not in_procedure:
                continue

            if self.lines.is_skippable(line):
                continue

            if not self.condition_scanner.is_condition_start(line):
                continue

            widest = max(widest, self.condition_size(lines, index))

        return widest


__all__ = ["OutputWriteGuard"]
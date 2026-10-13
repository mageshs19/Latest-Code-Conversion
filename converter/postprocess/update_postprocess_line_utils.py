"""Fixed-format line access for the update post-process.

CORRECTION 1 - rstrip() destroyed the body padding
----------------------------------------------------
    text = str(line or "").rstrip()

Trailing blanks are not decoration: they are what hold the right
sequence at column 73. A record whose columns 73-80 are blank was
stripped back to the end of its text, the len(text) >= 72 test then
took the OTHER branch, and the two branches do not agree.

Only the LINE ENDING is removed now.

CORRECTION 2 - two extraction rules for one question
------------------------------------------------------
    branch A   text[7:72]    starts AFTER the indicator
    branch B   text[6:]      INCLUDES the indicator

Which branch ran depended only on the line's length after the rstrip
above, so the same record produced two different bodies. There is one
rule now: columns 8-72, indicator excluded, exposed separately by
indicator() for callers that need it.

CORRECTION 3 - the trailing-digit strip ate numeric literals
--------------------------------------------------------------
    if len(body) >= 8 and body[-8:].strip().isdigit():
        body = body[:-8]

A heuristic cannot tell a sequence number from a literal. The generated
output contains

    003010     MOVE 00010101

the DB2 minimum date, split across two physical lines. This rule
returned "MOVE" and deleted the literal. Columns are geometry, not a
guess: the right sequence lives at 73-80 and nowhere else.

CORRECTION 4 - the class could read a line but not write one
--------------------------------------------------------------
Four managers emit lines - copybook include, main flow, restart
paragraphs and date working storage - and none had a shared builder, so
each reassembled records itself and each left the SOURCE line's right
sequence inside the body:

    000480     COPY VMDZ205I. 00480000
    002340     STOP RUN. 02350000
    002960     MOVE ZEROES TO DA-CCYYMMDD 02960000

The resequencer then wrote a fresh sequence at 73-80 and the old one
was stranded as a numeric literal after a complete statement. Nine to
forty-six such lines per generated member; zero in members that did not
run this pass.

replace_body() is now the ONE way to write a line here. It reassembles
from the record's own sequence areas and refuses rather than truncate.
"""

from __future__ import annotations

import re

from converter.services.fixed_format_line_service import (
    FixedFormatLineService,
)
from patterns.update_restart_patterns import (
    COPY_INCLUDE_TOKEN_PATTERN_TEMPLATE,
    END_PROGRAM_PATTERN,
    LINKAGE_SECTION_PATTERN,
    PARAGRAPH_HEADER_PATTERN,
    PROCEDURE_DIVISION_PATTERN,
    WORKING_STORAGE_SECTION_PATTERN,
)

LINE_ENDINGS = "\r\n"
SEQUENCE_WIDTH = 6
INDICATOR_COLUMN = 6
BODY_FIRST_INDEX = 7
BODY_LAST_INDEX = 72
COMMENT_INDICATORS = ("*", "/")
BLANK_INDICATOR = " "


class UpdatePostprocessLineUtils:
    def __init__(self, fixed_format: FixedFormatLineService | None = None) -> None:
        self.fixed_format = fixed_format or FixedFormatLineService()

    #
    # Reading
    #
    def lines(self, text: str) -> list[str]:
        return (
            str(text or "")
            .replace("\r\n", "\n")
            .replace("\r", "\n")
            .splitlines()
        )

    def join(self, lines: list[str]) -> str:
        return "\n".join(lines).rstrip() + "\n"

    def is_sequenced(self, line: str) -> bool:
        text = str(line or "").rstrip(LINE_ENDINGS)
        return (
            len(text) > INDICATOR_COLUMN
            and text[:SEQUENCE_WIDTH].strip().isdigit()
        )

    def indicator(self, line: str) -> str:
        text = str(line or "").rstrip(LINE_ENDINGS)
        if not self.is_sequenced(text):
            return BLANK_INDICATOR
        return text[INDICATOR_COLUMN : INDICATOR_COLUMN + 1] or BLANK_INDICATOR

    def is_comment(self, line: str) -> bool:
        return self.indicator(line) in COMMENT_INDICATORS

    def logical(self, line: str) -> str:
        """Columns 8-72, indicator excluded. ONE rule, no heuristics."""
        text = str(line or "").rstrip(LINE_ENDINGS)

        if not self.is_sequenced(text):
            return text.strip()

        return text[BODY_FIRST_INDEX:BODY_LAST_INDEX].strip()

    def logical_text(self, cobol_text: str) -> str:
        return "\n".join(
            self.logical(line) for line in self.lines(cobol_text)
        )

    def logical_contains(self, cobol_text: str, expected: str) -> bool:
        target = str(expected or "").strip().upper()
        if not target:
            return False
        for line in self.lines(cobol_text):
            if target in self.logical(line).upper():
                return True
        return False

    def contains_copy(self, cobol_text: str, include_name: str) -> bool:
        target = str(include_name or "").strip().upper()
        if not target:
            return False
        pattern = re.compile(
            COPY_INCLUDE_TOKEN_PATTERN_TEMPLATE.format(
                include_name=re.escape(target),
            ),
            flags=re.IGNORECASE,
        )
        return bool(pattern.search(self.logical_text(cobol_text)))

    #
    # Writing - CORRECTION 4. The one way to emit a line.
    #
    def replace_body(self, reference_line: str, body: str) -> str:
        """`reference_line` with columns 8-72 replaced by `body`.

        The record is reassembled from its OWN left sequence, indicator
        and right sequence, so a rewritten line can never carry a stale
        sequence number into its body, and never grows past 80 columns.

        Returns the reference line UNCHANGED when the new body does not
        fit columns 8-72. A refusal leaves working code; a truncated
        data-name does not.
        """
        reference = str(reference_line or "").rstrip(LINE_ENDINGS)
        text = str(body or "")

        if not self.is_sequenced(reference):
            return text.rstrip()

        try:
            left, indicator, _old_body, right = self.fixed_format.split(reference)
            rebuilt = self.fixed_format.build_or_none(
                str(left or ""),
                str(indicator or BLANK_INDICATOR),
                text,
                str(right or ""),
            )
        except Exception:  # noqa: BLE001 - one odd line must not abort a pass
            rebuilt = None

        return rebuilt if rebuilt is not None else reference

    #
    # Location
    #
    def data_division_insert_line_index(self, lines: list[str]) -> int:
        for index, line in enumerate(lines):
            if LINKAGE_SECTION_PATTERN.match(self.logical(line)):
                return index
        for index, line in enumerate(lines):
            if PROCEDURE_DIVISION_PATTERN.match(self.logical(line)):
                return index
        for index, line in enumerate(lines):
            if WORKING_STORAGE_SECTION_PATTERN.match(self.logical(line)):
                return index + 1
        return -1

    def procedure_paragraph_insert_line_index(self, lines: list[str]) -> int:
        for index, line in enumerate(lines):
            if END_PROGRAM_PATTERN.match(self.logical(line)):
                return index
        for line in lines:
            if PROCEDURE_DIVISION_PATTERN.match(self.logical(line)):
                return len(lines)
        return -1

    def find_paragraph_range(
        self,
        lines: list[str],
        paragraph_name: str,
    ) -> tuple[int, int] | None:
        target = str(paragraph_name or "").upper().rstrip(".")

        for index, line in enumerate(lines):
            if self.logical(line).upper().rstrip(".") != target:
                continue

            end = index + 1
            while end < len(lines):
                next_logical = self.logical(lines[end]).strip()
                if end > index + 1 and PARAGRAPH_HEADER_PATTERN.match(next_logical):
                    break
                end += 1

            return index, end

        return None


__all__ = ["UpdatePostprocessLineUtils"]
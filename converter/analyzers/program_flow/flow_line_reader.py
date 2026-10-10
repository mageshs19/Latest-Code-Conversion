# LOCATION: converter/analyzers/program_flow/flow_line_reader.py
# ACTION: CREATE NEW FILE
"""Turns raw COBOL records into LogicalLine values.

CORRECTION - comments were analysed as code.

The reader returned (number, logical, raw) and said nothing about the
indicator column, so every scanner downstream treated

    * OPZOEKEN VAN ALLE EVENEMENTEN BIJ EEN EFFECT

as an executable line. Comment narrative then fed the write and date
counts. Classification happens ONCE, here, reading column 7 of the RAW
record - which is where the indicator actually lives.
"""

from __future__ import annotations

from converter.analyzers.program_flow.flow_models import LogicalLine
from patterns.sequence_patterns import strip_sequence_numbers

INDICATOR_COLUMN = 6
COMMENT_INDICATORS = ("*", "/")


class FlowLineReader:
    """Reads a program into classified logical lines."""

    def read(self, cobol_text: str) -> list[LogicalLine]:
        output: list[LogicalLine] = []

        for number, raw in enumerate(str(cobol_text or "").splitlines(), start=1):
            record = raw.rstrip()
            output.append(
                LogicalLine(
                    number=number,
                    logical=strip_sequence_numbers(record),
                    raw=record,
                    is_comment=self._is_comment(record),
                )
            )

        return output

    @staticmethod
    def code_only(lines: list[LogicalLine]) -> list[LogicalLine]:
        """Executable lines only. Comments and blanks removed."""
        return [line for line in lines if not line.is_comment and line.body]

    @staticmethod
    def _is_comment(record: str) -> bool:
        """Column 7 of a sequenced record, else a leading indicator."""
        text = str(record or "")
        if len(text) > INDICATOR_COLUMN and text[:INDICATOR_COLUMN].strip().isdigit():
            return text[INDICATOR_COLUMN] in COMMENT_INDICATORS
        return text.lstrip()[:1] in COMMENT_INDICATORS


__all__ = ["FlowLineReader", "INDICATOR_COLUMN", "COMMENT_INDICATORS"]
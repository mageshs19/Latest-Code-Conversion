# LOCATION: converter/analyzers/program_flow/flow_paragraph_scanner.py
# ACTION: CREATE NEW FILE
"""Finds PROCEDURE DIVISION paragraphs and maps lines to their owner.

CORRECTION 1 - an empty span.

    current.end_line = line_number - 1

was written unguarded when one paragraph header immediately followed
another. end_line then fell BELOW start_line, range(start, end + 1) was
empty, and the header line itself belonged to no paragraph - so every
output write in a one-line paragraph was reported with no owner.

CORRECTION 2 - inconsistent stripping.

PROCEDURE_DIVISION_PATTERN was matched against the UNSTRIPPED logical
line while PARAGRAPH_PATTERN was matched against the stripped one. Both
read the same body now.
"""

from __future__ import annotations

from converter.analyzers.program_flow.flow_models import LogicalLine, ParagraphSpan
from patterns.cobol_patterns import PARAGRAPH_PATTERN, PROCEDURE_DIVISION_PATTERN


class FlowParagraphScanner:
    """Read-only paragraph discovery."""

    def spans(self, lines: list[LogicalLine]) -> list[ParagraphSpan]:
        output: list[ParagraphSpan] = []
        current: ParagraphSpan | None = None
        inside_procedure = False

        for line in lines or []:
            if line.is_comment:
                continue

            body = line.body
            if not body:
                continue

            if PROCEDURE_DIVISION_PATTERN.match(body):
                inside_procedure = True

            if not inside_procedure:
                continue

            match = PARAGRAPH_PATTERN.match(body)

            if match:
                if current is not None:
                    current.end_line = max(current.start_line, line.number - 1)
                    output.append(current)

                current = ParagraphSpan(
                    name=match.group("name").upper(),
                    start_line=line.number,
                    end_line=line.number,
                    lines=[line.raw],
                )
                continue

            if current is not None:
                current.lines.append(line.raw)
                current.end_line = line.number

        if current is not None:
            output.append(current)

        return output

    @staticmethod
    def name_by_line(paragraphs: list[ParagraphSpan]) -> dict[int, str]:
        """Line number -> owning paragraph name."""
        output: dict[int, str] = {}

        for paragraph in paragraphs or []:
            last = max(paragraph.start_line, paragraph.end_line)
            for number in range(paragraph.start_line, last + 1):
                output[number] = paragraph.name

        return output


__all__ = ["FlowParagraphScanner"]
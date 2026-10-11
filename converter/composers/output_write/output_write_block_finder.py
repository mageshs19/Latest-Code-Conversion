from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from converter.composers.output_write.output_write_line_utils import (
    OutputWriteLineUtils,
)
from converter.composers.output_write.output_write_scanner import (
    OutputWriteScanner,
)
from converter.services.cobol_condition_scanner import (
    CobolConditionScanner,
)

UNNAMED_PARAGRAPH = "(unnamed)"


@dataclass(frozen=True)
class CandidateBlock:
    if_index: int = -1
    end_index: int = -1
    paragraph: str = ""
    condition_end: int = -1

    @property
    def has_resolved_condition(self) -> bool:
        if self.condition_end < self.if_index:
            return False
        return self.condition_end < self.end_index

    @property
    def condition_line_count(self) -> int:
        if not self.has_resolved_condition:
            return 0
        return (self.condition_end - self.if_index) + 1

    @property
    def body_start(self) -> int:
        if self.has_resolved_condition:
            return self.condition_end + 1
        return self.if_index + 1

    @property
    def source(self) -> str:
        return self.paragraph or UNNAMED_PARAGRAPH

    def body(self, lines: list[str]) -> list[str]:
        return lines[self.body_start:self.end_index]


class OutputWriteBlockFinder:

    def __init__(
        self,
        line_utils: OutputWriteLineUtils | None = None,
        scanner: OutputWriteScanner | None = None,
        condition_scanner: CobolConditionScanner | None = None,
    ) -> None:
        self.lines = line_utils or OutputWriteLineUtils()
        self.scanner = scanner or OutputWriteScanner(self.lines)
        self.conditions = condition_scanner or CobolConditionScanner(
            fixed_format=self.lines.fixed_format,
        )

    def candidates(self, lines: list[str]) -> Iterator[CandidateBlock]:
        start = self.scanner.procedure_division_index(lines)
        if start < 0:
            return

        index = start + 1
        paragraph = ""

        while index < len(lines):
            logical = self.lines.logical(lines[index])

            if self.lines.is_division_boundary(logical):
                return

            header = self.lines.paragraph_name(lines[index])
            if header:
                paragraph = header
                index += 1
                continue

            if not self.scanner.is_condition_start(logical):
                index += 1
                continue

            end_index = self.scanner.matching_end_if(lines, index)
            if end_index >= 0:
                yield CandidateBlock(
                    if_index=index,
                    end_index=end_index,
                    paragraph=paragraph,
                    condition_end=self.conditions.condition_end_index(
                        lines, index
                    ),
                )

            index += 1


__all__ = ["UNNAMED_PARAGRAPH", "CandidateBlock", "OutputWriteBlockFinder"]
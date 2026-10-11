from __future__ import annotations

from typing import List, Tuple

from converter.generators.initialization.line_geometry import LineGeometry
from patterns.initialization_scope_patterns import (
    DIVISION_PATTERN,
    PARAGRAPH_HEADER_PATTERN,
    PROCEDURE_DIVISION_PATTERN,
    SECTION_HEADER_PATTERN,
)
from rules.initialization_placement_rules import NON_PARAGRAPH_WORDS

MAINLINE_NAME = ""


class ParagraphIndex:

    def __init__(self, geometry: LineGeometry | None = None) -> None:
        self.geometry = geometry or LineGeometry()

    def is_paragraph_header(self, line: str) -> bool:
        if self.geometry.is_comment_or_blank(line):
            return False
        body = self.geometry.body(line)
        if DIVISION_PATTERN.match(body):
            return False
        if SECTION_HEADER_PATTERN.match(body):
            return True
        match = PARAGRAPH_HEADER_PATTERN.match(body)
        if not match:
            return False
        return match.group("name").upper() not in NON_PARAGRAPH_WORDS

    def paragraph_name(self, line: str) -> str:
        body = self.geometry.body(line)
        match = (
            PARAGRAPH_HEADER_PATTERN.match(body)
            or SECTION_HEADER_PATTERN.match(body)
        )
        return match.group("name").upper() if match else ""

    def procedure_division_index(self, lines: List[str]) -> int:
        for index, line in enumerate(lines):
            if self.geometry.is_comment_or_blank(line):
                continue
            if PROCEDURE_DIVISION_PATTERN.match(self.geometry.body(line)):
                return index
        return -1

    def first_statement_index(self, lines: List[str], after: int) -> int:
        for index in range(after + 1, len(lines)):
            if not self.geometry.is_comment_or_blank(lines[index]):
                return index
        return -1

    def headers(self, lines: List[str]) -> List[Tuple[int, str]]:
        return [
            (index, self.paragraph_name(line))
            for index, line in enumerate(lines)
            if self.is_paragraph_header(line)
        ]

    def header_index(self, lines: List[str], name: str) -> int:
        target = str(name or "").upper()
        for index, header in self.headers(lines):
            if header == target:
                return index
        return -1

    def span_of(self, lines: List[str], start: int) -> Tuple[int, int]:
        if start < 0 or start >= len(lines):
            return (-1, -1)
        for index in range(start + 1, len(lines)):
            if self.is_paragraph_header(lines[index]):
                return (start, index - 1)
        return (start, len(lines) - 1)

    def span_named(self, lines: List[str], name: str) -> Tuple[int, int]:
        return self.span_of(lines, self.header_index(lines, name))

    def mainline_span(self, lines: List[str]) -> Tuple[int, int]:
        start = self.procedure_division_index(lines)
        if start < 0:
            return (-1, -1)
        for index in range(start + 1, len(lines)):
            if self.is_paragraph_header(lines[index]):
                return (start, index - 1)
        return (start, len(lines) - 1)

    def owner_of(self, lines: List[str], index: int) -> str:
        if index < 0 or index >= len(lines):
            return MAINLINE_NAME
        for position in range(index, -1, -1):
            if self.is_paragraph_header(lines[position]):
                return self.paragraph_name(lines[position])
            if PROCEDURE_DIVISION_PATTERN.match(
                self.geometry.body(lines[position])
            ):
                return MAINLINE_NAME
        return MAINLINE_NAME

    def is_mainline(self, lines: List[str], index: int) -> bool:
        return self.owner_of(lines, index) == MAINLINE_NAME


__all__ = ["ParagraphIndex", "MAINLINE_NAME"]
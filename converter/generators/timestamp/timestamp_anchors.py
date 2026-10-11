from __future__ import annotations

from typing import List

from converter.generators.initialization.line_geometry import LineGeometry
from patterns.timestamp_patterns import (
    END_PROGRAM_PATTERN,
    LINKAGE_SECTION_PATTERN,
    PROCEDURE_DIVISION_PATTERN,
    STOP_RUN_PATTERN,
    WORKING_STORAGE_PATTERN,
    declaration_pattern,
    paragraph_header_pattern,
    perform_pattern,
)

NOT_FOUND = -1


class TimestampAnchors:

    def __init__(self, geometry: LineGeometry | None = None) -> None:
        self.geometry = geometry or LineGeometry()

    def bodies(self, lines: List[str]) -> List[str]:
        return [self.geometry.body(line) for line in lines]

    def index_of(self, lines: List[str], pattern) -> int:
        for index, line in enumerate(lines):
            if self.geometry.is_comment_or_blank(line):
                continue
            if pattern.match(self.geometry.body(line)):
                return index
        return NOT_FOUND

    def procedure_division_index(self, lines: List[str]) -> int:
        return self.index_of(lines, PROCEDURE_DIVISION_PATTERN)

    def working_storage_index(self, lines: List[str]) -> int:
        return self.index_of(lines, WORKING_STORAGE_PATTERN)

    def linkage_section_index(self, lines: List[str]) -> int:
        return self.index_of(lines, LINKAGE_SECTION_PATTERN)

    def stop_run_index(self, lines: List[str]) -> int:
        return self.index_of(lines, STOP_RUN_PATTERN)

    def end_program_index(self, lines: List[str]) -> int:
        return self.index_of(lines, END_PROGRAM_PATTERN)

    def working_storage_insert_index(self, lines: List[str]) -> int:
        linkage = self.linkage_section_index(lines)
        if linkage >= 0:
            return linkage

        procedure = self.procedure_division_index(lines)
        if procedure >= 0:
            return procedure

        working_storage = self.working_storage_index(lines)
        if working_storage >= 0:
            return working_storage + 1

        return NOT_FOUND

    def paragraph_insert_index(self, lines: List[str]) -> int:
        end_program = self.end_program_index(lines)
        if end_program >= 0:
            return end_program
        return len(lines)

    def first_statement_index(self, lines: List[str], after: int) -> int:
        for index in range(after + 1, len(lines)):
            if not self.geometry.is_comment_or_blank(lines[index]):
                return index
        return NOT_FOUND

    def has_paragraph(self, lines: List[str], name: str) -> bool:
        return self.index_of(lines, paragraph_header_pattern(name)) >= 0

    def has_perform(self, lines: List[str], name: str) -> bool:
        return self.index_of(lines, perform_pattern(name)) >= 0

    def perform_count(self, lines: List[str], name: str) -> int:
        pattern = perform_pattern(name)
        count = 0
        for line in lines:
            if self.geometry.is_comment_or_blank(line):
                continue
            if pattern.match(self.geometry.body(line)):
                count += 1
        return count

    def declaration_level(self, lines: List[str], field: str) -> str:
        pattern = declaration_pattern(field)
        for line in lines:
            if self.geometry.is_comment_or_blank(line):
                continue
            match = pattern.match(self.geometry.body(line))
            if match:
                return match.group("level")
        return ""

    def has_marker(self, lines: List[str], marker: str) -> bool:
        target = str(marker or "").upper()
        return any(target in str(line or "").upper() for line in lines)


__all__ = ["TimestampAnchors", "NOT_FOUND"]
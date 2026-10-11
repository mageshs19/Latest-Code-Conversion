from __future__ import annotations

from typing import List, Set, Tuple

from converter.generators.initialization.line_geometry import LineGeometry
from patterns.initialization_scope_patterns import INITIALIZE_PATTERN
from rules.initialization_placement_rules import STATEMENT_TERMINATOR


class InitializeRemover:

    def __init__(self, geometry: LineGeometry | None = None) -> None:
        self.geometry = geometry or LineGeometry()

    def remove(
        self,
        lines: List[str],
        groups: Set[str],
    ) -> Tuple[List[str], int]:
        targets = {str(group or "").upper() for group in (groups or set())}
        if not targets:
            return list(lines), 0

        doomed = self._doomed_indexes(lines, targets)
        if not doomed:
            return list(lines), 0

        output: List[str] = []
        for index, line in enumerate(lines):
            if index not in doomed:
                output.append(line)
                continue
            if self._carries_terminator(line):
                self._restore_terminator(output)
        return output, len(doomed)

    def groups_present(self, lines: List[str]) -> Set[str]:
        found: Set[str] = set()
        for line in lines:
            if self.geometry.is_comment_or_blank(line):
                continue
            match = INITIALIZE_PATTERN.match(self.geometry.body(line))
            if match:
                found.add(match.group("group").upper())
        return found

    def _doomed_indexes(
        self,
        lines: List[str],
        targets: Set[str],
    ) -> Set[int]:
        doomed: Set[int] = set()
        for index, line in enumerate(lines):
            if self.geometry.is_comment_or_blank(line):
                continue
            match = INITIALIZE_PATTERN.match(self.geometry.body(line))
            if not match:
                continue
            if match.group("group").upper() in targets:
                doomed.add(index)
        return doomed

    def _carries_terminator(self, line: str) -> bool:
        return self.geometry.body(line).rstrip().endswith(
            STATEMENT_TERMINATOR
        )

    def _restore_terminator(self, output: List[str]) -> None:
        position = self._last_executable(output)
        if position < 0:
            return
        body = self.geometry.body(output[position]).rstrip()
        if not body or body.endswith(STATEMENT_TERMINATOR):
            return
        output[position] = self.geometry.replace_body(
            output[position],
            body + STATEMENT_TERMINATOR,
        )

    def _last_executable(self, output: List[str]) -> int:
        for position in range(len(output) - 1, -1, -1):
            if not self.geometry.is_comment_or_blank(output[position]):
                return position
        return -1


__all__ = ["InitializeRemover"]